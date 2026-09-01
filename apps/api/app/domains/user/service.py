"""User domain business orchestration."""

import uuid
from datetime import timedelta

from app.core.errors import (
    BusinessException,
    ErrorCode,
    raise_user_already_exists,
    raise_user_not_found,
)
from app.core.models import User
from app.core.security import create_access_token, verify_password
from app.domains.user import repository
from app.domains.user.schemas import (
    Token,
    UpdatePassword,
    UserCreate,
    UserRegister,
    UserUpdate,
    UserUpdateMe,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


async def authenticate(*, session: AsyncSession, email: str, password: str) -> User:
    user, upgraded = await repository.authenticate(session=session, email=email, password=password)
    if not user:
        raise BusinessException(
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise BusinessException(code=ErrorCode.AUTH_INACTIVE_USER, detail="Inactive user")
    # 密码哈希升级在认证通过后才 commit，避免无效用户的升级落盘
    if upgraded:
        await session.commit()
    return user


async def login(*, session: AsyncSession, email: str, password: str, expires_minutes: int) -> Token:
    user = await authenticate(session=session, email=email, password=password)
    return Token(
        access_token=create_access_token(
            user.id, expires_delta=timedelta(minutes=expires_minutes)
        )
    )


async def create_user(*, session: AsyncSession, user_in: UserCreate) -> User:
    if await repository.get_user_by_email(session=session, email=user_in.email):
        raise_user_already_exists("User with this email already exists")
    try:
        user = await repository.create_user(session=session, user_create=user_in)
        await session.commit()
        return user
    except IntegrityError:
        await session.rollback()
        raise_user_already_exists("User with this email already exists")


async def register_user(*, session: AsyncSession, user_in: UserRegister) -> User:
    if await repository.get_user_by_email(session=session, email=user_in.email):
        raise_user_already_exists("User with this email already exists")
    try:
        user = await repository.create_user(
            session=session, user_create=UserCreate.model_validate(user_in)
        )
        await session.commit()
        return user
    except IntegrityError:
        await session.rollback()
        raise_user_already_exists("User with this email already exists")


async def list_users(
    *, session: AsyncSession, skip: int, limit: int
) -> tuple[list[User], int]:
    return await repository.get_users(session=session, skip=skip, limit=limit)


async def update_me(*, session: AsyncSession, user: User, user_in: UserUpdateMe) -> User:
    if user_in.email:
        existing = await repository.get_user_by_email(session=session, email=user_in.email)
        if existing and existing.id != user.id:
            raise_user_already_exists("User with this email already exists")
    try:
        user = await repository.update_user_me(session=session, db_user=user, user_in=user_in)
        await session.commit()
        return user
    except IntegrityError:
        await session.rollback()
        raise BusinessException(
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            detail="Unable to update user",
        )


async def update_password(
    *, session: AsyncSession, user: User, body: UpdatePassword
) -> None:
    verified, _ = verify_password(body.current_password, user.hashed_password)
    if not verified:
        raise BusinessException(code=ErrorCode.USER_INVALID_PASSWORD, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise BusinessException(
            code=ErrorCode.USER_PASSWORD_SAME_AS_OLD,
            detail="New password cannot be the same as the current one",
        )
    try:
        await repository.update_password_me(
            session=session, db_user=user, new_password=body.new_password
        )
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise BusinessException(
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            detail="Unable to update password",
        )


async def update_user(
    *, session: AsyncSession, user_id: uuid.UUID, user_in: UserUpdate
) -> User:
    user = await repository.get_user(session=session, user_id=user_id)
    if user is None:
        raise_user_not_found("The user with this id does not exist in the system")
    if user_in.email:
        existing = await repository.get_user_by_email(session=session, email=user_in.email)
        if existing and existing.id != user_id:
            raise_user_already_exists("User with this email already exists")
    try:
        user = await repository.update_user(session=session, db_user=user, user_in=user_in)
        await session.commit()
        return user
    except IntegrityError:
        await session.rollback()
        raise_user_already_exists("User with this email already exists")


async def delete_user(
    *, session: AsyncSession, user: User | None = None, user_id: uuid.UUID | None = None, current_user: User | None = None
) -> None:
    """删除用户。支持传入 user 对象或 user_id（任一即可）。

    安全约束（最后超管保护）：
    - 超管不允许自删（保留显式 403，与原有行为兼容）。
    - 删除目标是超管时，统计剩余超管；若删除后为 0 则拒绝。
    """
    if user is None and user_id is None:
        raise ValueError("Either user or user_id must be provided")
    if user is None:
        user = await get_user(session=session, user_id=user_id)  # type: ignore[arg-type]
    # 超管自删：保留历史行为，显式 403
    if current_user is not None and user.id == current_user.id and current_user.is_superuser:
        raise BusinessException(
            code=ErrorCode.USER_CANNOT_DELETE_SELF,
            detail="Super users are not allowed to delete themselves",
        )
    # 最后超管保护：禁止删除系统中最后一个超管
    if user.is_superuser:
        superuser_count = await repository.count_superusers(session=session)
        if superuser_count <= 1:
            raise BusinessException(
                code=ErrorCode.SYSTEM_BAD_REQUEST,
                detail="Cannot delete the last superuser",
            )
    await repository.delete_user(session=session, db_user=user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise BusinessException(
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            detail="Unable to delete user",
        )


async def get_user(*, session: AsyncSession, user_id: uuid.UUID) -> User:
    user = await repository.get_user(session=session, user_id=user_id)
    if user is None:
        raise_user_not_found()
    return user
