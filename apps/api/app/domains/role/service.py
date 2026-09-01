"""Role domain business orchestration."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import (
    BusinessException,
    ErrorCode,
    raise_role_already_exists,
    raise_role_not_found,
)
from app.core.models import Role
from app.domains.role import repository
from app.domains.role.schemas import RoleCreate, RoleUpdate


async def list_roles(
    *, session: AsyncSession, skip: int = 0, limit: int = 100
) -> tuple[list[Role], int]:
    return await repository.get_roles(session=session, skip=skip, limit=limit)


async def get_role(*, session: AsyncSession, role_id: uuid.UUID) -> Role:
    role = await repository.get_role(session=session, role_id=role_id)
    if role is None:
        raise_role_not_found()
    return role


async def create_role(*, session: AsyncSession, role_in: RoleCreate) -> Role:
    if await repository.get_role_by_name(session=session, name=role_in.name):
        raise_role_already_exists(f"Role with name '{role_in.name}' already exists")
    try:
        role = await repository.create_role(session=session, role_in=role_in)
        await session.commit()
        return role
    except IntegrityError:
        await session.rollback()
        raise_role_already_exists(f"Role with name '{role_in.name}' already exists")


async def update_role(
    *, session: AsyncSession, role_id: uuid.UUID, role_in: RoleUpdate
) -> Role:
    role = await get_role(session=session, role_id=role_id)
    if role_in.name and role_in.name != role.name:
        existing = await repository.get_role_by_name(session=session, name=role_in.name)
        if existing and existing.id != role_id:
            raise_role_already_exists(f"Role with name '{role_in.name}' already exists")
    try:
        updated = await repository.update_role(
            session=session, db_role=role, role_in=role_in
        )
        await session.commit()
        return updated
    except IntegrityError:
        await session.rollback()
        raise_role_already_exists(f"Role with name '{role_in.name}' already exists")


async def delete_role(*, session: AsyncSession, role_id: uuid.UUID) -> None:
    role = await get_role(session=session, role_id=role_id)
    await repository.delete_role(session=session, db_role=role)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise BusinessException(
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            detail="Unable to delete role",
        )
