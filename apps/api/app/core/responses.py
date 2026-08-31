"""统一 API 响应组装工具。"""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_user_scopes, get_users_scopes
from app.core.models import Role, User
from app.domains.role.repository import get_role_scopes_by_ids
from app.domains.role.schemas import RolePublic
from app.domains.user.schemas import UserPublic


async def user_public(
    *,
    session: AsyncSession,
    user: User,
) -> UserPublic:
    """将单个用户模型组装为公开响应。"""
    scopes = await get_user_scopes(session, user)
    return UserPublic.model_validate(user, update={"scopes": sorted(scopes)})


async def users_public(
    *,
    session: AsyncSession,
    users: Sequence[User],
) -> list[UserPublic]:
    """批量组装用户公开响应，避免逐用户查询 scope。"""
    scopes_by_user = await get_users_scopes(
        session,
        [user.id for user in users],
    )
    return [
        UserPublic.model_validate(
            user,
            update={"scopes": sorted(scopes_by_user.get(user.id, set()))},
        )
        for user in users
    ]


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


def total_pages(*, count: int, page_size: int) -> int:
    """计算分页总页数，空结果保持返回 0。"""
    return (count + page_size - 1) // page_size if count > 0 else 0


def paginated_fields(*, count: int, page: int, page_size: int) -> dict[str, int]:
    """返回统一分页元数据，供各领域响应模型复用。"""
    return {
        "count": count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(count=count, page_size=page_size),
    }
