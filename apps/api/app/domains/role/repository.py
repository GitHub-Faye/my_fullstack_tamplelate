"""
Role 领域仓库层（Repository）

负责角色的数据库 CRUD 操作：
- get_role: 按 ID 查询单个角色（含 scopes）
- get_roles: 分页查询角色列表（含各角色的 scopes）
- create_role: 创建角色（name + scopes，两处写入同一事务）
- update_role: 更新角色（name 和/或 scopes，scopes 整体替换）
- delete_role: 删除角色（RoleScopeModel 级联删除）

说明：
- Role 与 RoleScopeModel 是一对多关系，角色名唯一（Role.name 带唯一索引）。
- 更新 scopes 使用「先删后插」策略：删除旧的 RoleScopeModel 记录后，
  用传入的完整 scope 集合重建，实现整体替换而非增量合并。
- scope 合法性校验统一走 app.core.scopes.ALL_SCOPES，
  与系统 scope 定义（user:read 等）保持一致。
"""

import uuid

from app.core.errors import raise_bad_request
from app.core.models import Role, RoleScopeModel
from app.core.scopes import ALL_SCOPES, BUILTIN_ROLES
from app.domains.role.schemas import RoleCreate, RoleUpdate
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

# ============================== Role CRUD Operations ==============================

async def _validate_scopes(session: AsyncSession, scopes: list[str]) -> list[str]:
    """
    校验 scope 集合是否全部在系统定义范围内。

    参数：
    - session: 数据库会话（备用，为将来扩展动态 scope 校验预留）
    - scopes: 待校验的 scope 列表（去重后返回）

    异常：
    - 400: 存在未在 ALL_SCOPES 中定义的 scope
    """
    valid = {scope.value for scope in ALL_SCOPES}
    unknown = [scope for scope in scopes if scope not in valid]
    if unknown:
        raise_bad_request(
            f"Unknown scopes: {unknown}. Valid scopes: {sorted(valid)}"
        )
    # 去重并保持传入顺序
    return list(dict.fromkeys(scopes))


async def get_role_scopes_by_ids(
    session: AsyncSession,
    role_ids: list[uuid.UUID],
) -> dict[uuid.UUID, list[str]]:
    """批量查询角色 scope，结果包含无 scope 角色的空列表。"""
    scopes_by_role = {role_id: [] for role_id in role_ids}
    if not role_ids:
        return scopes_by_role

    statement = (
        select(RoleScopeModel.role_id, RoleScopeModel.scope)
        .where(RoleScopeModel.role_id.in_(role_ids))
        .order_by(RoleScopeModel.role_id, RoleScopeModel.scope)
    )
    result = await session.execute(statement)
    for role_id, scope in result.all():
        scopes_by_role[role_id].append(scope)
    return scopes_by_role


async def get_role(*, session: AsyncSession, role_id: uuid.UUID) -> Role | None:
    """
    按 ID 查询角色。

    返回：
    - Role 数据库对象（不含 scopes，scopes 由调用方通过 get_role_scopes_by_ids 补全）
    - 不存在时返回 None
    """
    return await session.get(Role, role_id)


async def get_roles(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Role], int]:
    """
    分页查询角色列表。

    返回：
    - (角色列表, 总数)
    """
    # 构建总数查询
    count_statement = select(func.count()).select_from(Role)
    result = await session.execute(count_statement)
    count = result.scalar_one()

    # 构建列表查询
    # order_by(Role.created_at.asc()) 有类型误报，运行时正确；用 desc 与用户列表保持一致
    statement = select(Role).order_by(Role.created_at.desc())  # type: ignore[arg-type,union-attr]
    statement = statement.offset(skip).limit(limit)
    result = await session.execute(statement)
    roles = result.scalars().all()

    return list(roles), int(count)


async def create_role(
    *,
    session: AsyncSession,
    role_in: RoleCreate,
) -> Role:
    """
    创建新角色（name + scopes 在同一事务内写入）。

    参数：
    - role_in: 角色创建 DTO（name 必填，scopes 可选）

    返回：
    - 创建成功的 Role 对象

    注意：
    - 调用方需先检查 name 唯一性
    - 传入的 scopes 会被去重并校验合法性
    """
    valid_scopes = await _validate_scopes(session, role_in.scopes)

    db_role = Role(name=role_in.name)
    session.add(db_role)
    await session.flush()  # 获取 role.id

    # 写入 scopes（RoleScopeModel 关联表）
    for scope_value in valid_scopes:
        session.add(RoleScopeModel(role_id=db_role.id, scope=scope_value))

    return db_role


async def update_role(
    *,
    session: AsyncSession,
    db_role: Role,
    role_in: RoleUpdate,
) -> Role:
    """
    更新角色：修改 name 和/或整体替换 scopes。

    参数：
    - db_role: 已存在的角色数据库对象
    - role_in: 角色更新 DTO（name、scopes 均可选）

    返回：
    - 更新后的 Role 对象

    业务规则：
    - 未设置的字段保持不变（部分更新）。
    - 一旦传入 scopes，则「整体替换」：删除全部旧 RoleScopeModel 后重建，
      实现增减 scope 的效果（满足"修改角色的同时修改其持有的 scope"）。
    - 不允许删除系统预置角色（viewer / editor / admin）——
      init_roles_and_scopes 依赖它们，且它们被新用户默认引用。
    """
    # 防止删除系统预置角色（其 scopes 由代码初始化时定义，删除会导致初始化逻辑失效）
    if db_role.name in BUILTIN_ROLES:
        raise_bad_request(
            f"Built-in role '{db_role.name}' cannot be modified"
        )

    update_data = role_in.model_dump(exclude_unset=True)

    # 处理名称更新
    if update_data.get("name"):
        db_role.name = update_data["name"]

    # 处理 scopes 整体替换（先删后插，保证与传入集合一致）
    scope_values = update_data.get("scopes")
    if scope_values is not None:
        valid_scopes = await _validate_scopes(session, scope_values)

        # 删除旧的 RoleScopeModel 记录
        statement = delete(RoleScopeModel).where(RoleScopeModel.role_id == db_role.id)  # type: ignore[arg-type]
        await session.execute(statement)

        # 重建 scopes（整体替换）
        for scope_value in valid_scopes:
            session.add(RoleScopeModel(role_id=db_role.id, scope=scope_value))

    session.add(db_role)
    await session.flush()
    return db_role


async def delete_role(*, session: AsyncSession, db_role: Role) -> None:
    """
    删除角色。

    注意：
    - RoleScopeModel 通过外键 ondelete="CASCADE" 级联删除。
    - 删除前需确保没有用户引用此角色（UserRole 外键为 CASCADE，
      删除角色会自动解除用户与角色的关联）。
    - 系统预置角色（viewer / editor / admin）不允许删除。
    """
    # 防止删除系统预置角色
    if db_role.name in BUILTIN_ROLES:
        raise_bad_request(
            f"Built-in role '{db_role.name}' cannot be deleted"
        )

    await session.delete(db_role)


async def get_role_by_name(*, session: AsyncSession, name: str) -> Role | None:
    """
    按名称查询角色（用于唯一性校验）。
    """
    statement = select(Role).where(Role.name == name)  # type: ignore[arg-type]
    result = await session.execute(statement)
    return result.scalar_one_or_none()