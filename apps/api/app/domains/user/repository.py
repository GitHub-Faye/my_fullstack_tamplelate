from typing import Any, Tuple
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import get_password_hash, verify_password
from app.domains.user.schemas import UserCreate, UserUpdate, UserUpdateMe, UpdatePassword
from app.core.models import User, Item, AuditLog, Role, UserRole, UserRoleType

# ============================== 用户 CRUD 操作 ==============================
async def get_user(*, session: AsyncSession, user_id: uuid.UUID) -> User | None:
    """
    通过用户ID查询用户。
    - 使用 select + where 构建查询语句
    - 返回首条匹配结果，若不存在则返回 None
    """
    user = await session.get(User, user_id)
    return user

async def get_users(
    *, session: AsyncSession, skip: int, limit: int, sort_field: str = "created_at", sort_order: str = "desc"
) -> Tuple[list[User], int]:
    """
    分页获取用户列表
    
    Args:
        session: 数据库会话
        skip: 跳过的记录数
        limit: 返回的记录数
        sort_field: 排序字段
        sort_order: 排序方式 ("asc" 或 "desc")
    
    Returns:
        tuple: (用户列表, 总记录数)
    """
    # 获取用户总数
    count_statement = select(func.count()).select_from(User)
    result = await session.execute(count_statement)
    count = result.scalar_one()

    # 获取分页的用户列表
    statement = select(User)
    
    # 添加排序
    if hasattr(User, sort_field):
        if sort_order.lower() == "desc":
            statement = statement.order_by(getattr(User, sort_field).desc())
        else:
            statement = statement.order_by(getattr(User, sort_field).asc())
    else:
        # 默认按创建时间倒序排列
        statement = statement.order_by(User.created_at.desc())
    
    statement = statement.offset(skip).limit(limit)
    result = await session.execute(statement)
    users = result.scalars().all()

    return users, count


async def create_user(*, session: AsyncSession, user_create: UserCreate) -> User:
    """
    创建新用户。
    - 调用 get_password_hash 对明文密码进行哈希
    - 使用 model_validate 转换请求 DTO 为数据库模型
    - 插入数据库并返回完整的用户对象
    """
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def update_user(*, session: AsyncSession, db_user: User, user_in: UserUpdate) -> Any:
    """
    更新已有用户信息。
    - model_dump(exclude_unset=True)：仅取用户明确设置的字段（跳过未设置的可选字段）
    - 如果包含 password 字段，单独处理：先哈希再更新
    - sqlmodel_update 合并旧数据和新数据
    """
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def update_user_me(
    *, session: AsyncSession, db_user: User, user_in: UserUpdateMe
) -> User:
    """
    更新当前用户自己的信息。
    
    Args:
        session: 数据库会话
        db_user: 数据库用户对象
        user_in: 用户更新数据
    
    Returns:
        更新后的用户对象
    """
    # 仅序列化用户明确设置的字段
    user_data = user_in.model_dump(exclude_unset=True)
    # 使用 sqlmodel_update() 合并数据
    db_user.sqlmodel_update(user_data)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def update_password_me(
    *, session: AsyncSession, db_user: User, new_password: str
) -> User:
    """
    更新当前用户自己的密码。
    
    Args:
        session: 数据库会话
        db_user: 数据库用户对象
        new_password: 新密码
    
    Returns:
        更新后的用户对象
    """
    # 哈希新密码并保存
    hashed_password = get_password_hash(new_password)
    db_user.hashed_password = hashed_password
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def delete_user(*, session: AsyncSession, db_user: User) -> None:
    """
    删除指定用户。
    
    Args:
        session: 数据库会话
        db_user: 要删除的用户对象
    """
    await session.delete(db_user)
    await session.commit()


async def delete_user_items(*, session: AsyncSession, user_id: uuid.UUID) -> None:
    """
    删除指定用户的所有关联项目。
    
    Args:
        session: 数据库会话
        user_id: 用户ID
    """
    statement = delete(Item).where(Item.owner_id == user_id)
    await session.execute(statement)
    await session.commit()


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    """
    通过邮箱查询用户。
    - 使用 select + where 构建查询语句
    - 返回首条匹配结果，若不存在则返回 None
    """
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    session_user = result.scalar_one_or_none()
    return session_user


# 虚拟哈希值：用于防止时序攻击
# Argon2 哈希，用户不存在时也会执行相同耗时的密码验证逻辑，保证响应时间一致
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


async def authenticate(*, session: AsyncSession, email: str, password: str) -> User | None:
    """
    认证用户（登录验证）。
    - 首先按邮箱查询用户
    - 若用户不存在，仍执行虚拟密码验证（防止时序攻击）
    - 若用户存在，验证密码；密码正确则返回用户对象
    - verify_password 可能返回更新后的哈希值（密钥拉伸升级），如有则更新到数据库
    """
    db_user = await get_user_by_email(session=session, email=email)
    if not db_user:
        # 用户不存在时，也运行密码验证以保持恒定的响应时间（防时序攻击）
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    if updated_password_hash:
        # Argon2 参数升级时更新哈希值
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
    return db_user


# ============================== 审计日志操作 ==============================

async def create_audit_log(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    action: str,
    target_type: str,
    target_id: str | None = None,
    details: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """
    创建操作审计日志。

    Args:
        session: 数据库会话
        user_id: 操作人ID
        action: 操作类型（如 user.create, user.toggle_active）
        target_type: 操作对象类型
        target_id: 操作对象ID
        details: 操作详情
        ip_address: 操作IP

    Returns:
        创建的审计日志对象
    """
    log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def get_audit_logs(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    target_type: str | None = None,
    user_id: uuid.UUID | None = None,
) -> Tuple[list[AuditLog], int]:
    """
    获取操作审计日志列表（分页）。

    Args:
        session: 数据库会话
        skip: 跳过的记录数
        limit: 返回的记录数
        target_type: 筛选目标类型
        user_id: 筛选操作人

    Returns:
        tuple: (审计日志列表, 总记录数)
    """
    conditions = []
    if target_type:
        conditions.append(AuditLog.target_type == target_type)
    if user_id:
        conditions.append(AuditLog.user_id == user_id)

    from sqlalchemy import and_

    # 获取总数
    count_stmt = select(func.count()).select_from(AuditLog)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    result = await session.execute(count_stmt)
    count = result.scalar_one()

    # 获取分页数据
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    logs = result.scalars().all()

    return list(logs), count


# ============================== 管理员用户操作 ==============================

async def create_user_with_role(
    *,
    session: AsyncSession,
    user_create: "UserAdminCreate",
) -> User:
    """
    管理员创建用户（带角色分配和工资字段）。

    Args:
        session: 数据库会话
        user_create: 管理员创建用户 DTO

    Returns:
        创建的用户对象
    """
    user_data = user_create.model_dump(exclude={"password"})
    user_data["hashed_password"] = get_password_hash(user_create.password)
    db_obj = User(**user_data)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def assign_user_role(
    *,
    session: AsyncSession,
    user: User,
    role_name: str,
) -> None:
    """
    为用户分配角色。

    Args:
        session: 数据库会话
        user: 用户对象
        role_name: 角色名称（如 engineer, pm, admin_role）
    """
    # 查找或创建角色
    stmt = select(Role).where(Role.name == role_name)
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()

    if not role:
        role = Role(name=role_name)
        session.add(role)
        await session.flush()

    # 创建关联
    user_role = UserRole(user_id=user.id, role_id=role.id)
    session.add(user_role)
    await session.commit()


async def admin_update_user(
    *,
    session: AsyncSession,
    db_user: User,
    user_in: "UserAdminUpdate",
) -> User:
    """
    管理员更新用户信息。

    Args:
        session: 数据库会话
        db_user: 要更新的用户
        user_in: 更新 DTO

    Returns:
        更新后的用户对象
    """
    user_data = user_in.model_dump(exclude_unset=True)
    db_user.sqlmodel_update(user_data)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def update_user_role(
    *,
    session: AsyncSession,
    user: User,
    new_role: UserRoleType,
) -> None:
    """
    更新用户的角色关联（UserRole 表）。

    删除旧角色关联，创建新角色关联。

    Args:
        session: 数据库会话
        user: 用户对象
        new_role: 新角色类型
    """
    # 删除旧的 UserRole 关联
    from sqlalchemy import delete as sa_delete
    stmt = sa_delete(UserRole).where(UserRole.user_id == user.id)
    await session.execute(stmt)

    # 确定新的角色名称
    role_mapping = {
        UserRoleType.ENGINEER: "engineer",
        UserRoleType.PM: "pm",
        UserRoleType.ADMIN: "admin_role",
    }
    role_name = role_mapping.get(new_role, "engineer")

    # 查找或创建角色
    rstmt = select(Role).where(Role.name == role_name)
    result = await session.execute(rstmt)
    role = result.scalar_one_or_none()

    if not role:
        role = Role(name=role_name)
        session.add(role)
        await session.flush()

    # 创建新关联
    user_role = UserRole(user_id=user.id, role_id=role.id)
    session.add(user_role)
    await session.commit()


async def admin_reset_password(
    *,
    session: AsyncSession,
    db_user: User,
    new_password: str,
) -> User:
    """
    管理员重置用户密码。

    Args:
        session: 数据库会话
        db_user: 目标用户
        new_password: 新密码（明文）

    Returns:
        更新后的用户对象
    """
    db_user.hashed_password = get_password_hash(new_password)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def toggle_user_active(
    *,
    session: AsyncSession,
    db_user: User,
    is_active: bool,
) -> User:
    """
    启用/禁用用户账号。

    Args:
        session: 数据库会话
        db_user: 目标用户
        is_active: True 启用, False 禁用

    Returns:
        更新后的用户对象
    """
    db_user.is_active = is_active
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def get_user_detail(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
) -> User | None:
    """
    获取用户详情（包含工资字段）。

    Args:
        session: 数据库会话
        user_id: 用户ID

    Returns:
        用户对象或 None
    """
    return await session.get(User, user_id)
