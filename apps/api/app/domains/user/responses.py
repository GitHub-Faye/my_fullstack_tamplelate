"""User domain response assembly."""

from collections.abc import Sequence

from app.core.dependencies import get_user_scopes, get_users_scopes
from app.core.models import User
from app.domains.user.schemas import UserPublic
from sqlalchemy.ext.asyncio import AsyncSession


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
