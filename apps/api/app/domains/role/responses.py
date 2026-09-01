"""Role domain response assembly."""

from collections.abc import Sequence

from app.core.models import Role
from app.domains.role.repository import get_role_scopes_by_ids
from app.domains.role.schemas import RolePublic
from sqlalchemy.ext.asyncio import AsyncSession


async def role_public(
    *,
    session: AsyncSession,
    role: Role,
) -> RolePublic:
    """将单个角色模型组装为公开响应。"""
    scopes_by_role = await get_role_scopes_by_ids(session, [role.id])
    return RolePublic.model_validate(
        role,
        update={"scopes": scopes_by_role.get(role.id, [])},
    )


async def roles_public(
    *,
    session: AsyncSession,
    roles: Sequence[Role],
) -> list[RolePublic]:
    """批量组装角色公开响应，避免逐角色查询 scope。"""
    scopes_by_role = await get_role_scopes_by_ids(
        session,
        [role.id for role in roles],
    )
    return [
        RolePublic.model_validate(
            role,
            update={"scopes": scopes_by_role.get(role.id, [])},
        )
        for role in roles
    ]
