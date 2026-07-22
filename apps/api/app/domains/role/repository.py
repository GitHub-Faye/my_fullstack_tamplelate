"""
角色管理模块 — 数据访问层

提供角色 CRUD 操作：
- create_role: 创建角色（含 scopes）
- get_role: 获取单个角色（含 scopes）
- get_roles: 获取角色列表（分页）
- update_role: 更新角色（替换 scopes）
- delete_role: 删除角色
"""
import uuid
from typing import Tuple

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import Role, RoleScope


async def _reload_role_with_scopes(
    *,
    session: AsyncSession,
    role_id: uuid.UUID,
) -> Role:
    """重新查询角色及其 scopes 关系"""
    stmt = (
        select(Role)
        .options(selectinload(Role.scopes))
        .where(Role.id == role_id)
    )
    result = await session.execute(stmt)
    return result.unique().scalar_one()


async def get_role(
    *,
    session: AsyncSession,
    role_id: uuid.UUID,
) -> Role | None:
    """获取单个角色（含 scopes）"""
    stmt = (
        select(Role)
        .options(selectinload(Role.scopes))
        .where(Role.id == role_id)
    )
    result = await session.execute(stmt)
    return result.unique().scalar_one_or_none()


async def get_role_by_name(
    *,
    session: AsyncSession,
    name: str,
) -> Role | None:
    """通过名称查找角色"""
    stmt = select(Role).where(Role.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_roles(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[list[Role], int]:
    """获取角色列表（分页），含 scopes"""
    # 获取总数
    count_stmt = select(func.count(Role.id))
    count_result = await session.execute(count_stmt)
    count = count_result.scalar_one()

    # 获取分页数据（使用 selectinload 在 async 中需要确保在 session 内使用）
    stmt = (
        select(Role)
        .options(selectinload(Role.scopes))
        .offset(skip)
        .limit(limit)
        .order_by(Role.created_at.desc())
    )
    result = await session.execute(stmt)
    roles = list(result.scalars().unique().all())

    return roles, count


async def create_role(
    *,
    session: AsyncSession,
    name: str,
    scopes: list[str],
) -> Role:
    """创建角色并关联 scopes"""
    role = Role(name=name)
    session.add(role)
    await session.flush()

    for scope_value in scopes:
        role_scope = RoleScope(scope=scope_value, role_id=role.id)
        session.add(role_scope)

    await session.commit()

    return await _reload_role_with_scopes(session=session, role_id=role.id)


async def update_role(
    *,
    session: AsyncSession,
    role: Role,
    name: str | None = None,
    scopes: list[str] | None = None,
) -> Role:
    """更新角色名称和/或 scopes"""
    if name is not None:
        role.name = name

    if scopes is not None:
        # 删除旧 scopes
        stmt = delete(RoleScope).where(RoleScope.role_id == role.id)
        await session.execute(stmt)

        # 创建新 scopes
        for scope_value in scopes:
            role_scope = RoleScope(scope=scope_value, role_id=role.id)
            session.add(role_scope)

    await session.commit()

    # 重新查询以加载 scopes 关系
    role_id = role.id
    session.expire(role)
    return await _reload_role_with_scopes(
        session=session, role_id=role_id
    )


async def delete_role(
    *,
    session: AsyncSession,
    role: Role,
) -> None:
    """删除角色（级联删除关联的 scopes）"""
    await session.delete(role)
    await session.commit()
