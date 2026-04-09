import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.domains.user.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
    require_any_scope,
    check_item_owner_or_admin,
)
from app.core.models import Item
from app.core.scopes import ItemScope
from app.core.schemas import Message
from app.core.errors import raise_item_not_found
from app.domains.item.schemas import (
    ItemCreate,
    ItemPublic,
    ItemsPublic,
    ItemUpdate,
)

router = APIRouter()


@router.get(
    "/",
    response_model=ItemsPublic,
    dependencies=[Depends(require_any_scope(ItemScope.READ, ItemScope.ADMIN))],
)
async def read_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve items.
    
    - 普通用户只能查看自己的 items
    - 拥有 item:admin 权限的用户可以查看所有 items
    """
    # 检查是否有 admin 权限
    user_scopes = await check_item_owner_or_admin.__wrapped__(session, current_user, current_user.id)
    # 重新获取用户 scopes 来判断是否是 admin
    from app.domains.user.dependencies import get_user_scopes
    scopes = await get_user_scopes(session, current_user)
    is_admin = ItemScope.ADMIN.value in scopes or current_user.is_superuser

    if is_admin:
        count_statement = select(func.count()).select_from(Item)
        result = await session.execute(count_statement)
        count = result.scalar_one()
        statement = (
            select(Item).order_by(Item.created_at.desc()).offset(skip).limit(limit)
        )
        result = await session.execute(statement)
        items = result.scalars().all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Item)
            .where(Item.owner_id == current_user.id)
        )
        result = await session.execute(count_statement)
        count = result.scalar_one()
        statement = (
            select(Item)
            .where(Item.owner_id == current_user.id)
            .order_by(Item.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(statement)
        items = result.scalars().all()

    return ItemsPublic(data=items, count=count)


@router.get(
    "/{id}",
    response_model=ItemPublic,
    dependencies=[Depends(require_any_scope(ItemScope.READ, ItemScope.ADMIN))],
)
async def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get item by ID.
    
    - 普通用户只能查看自己的 item
    - 拥有 item:admin 权限的用户可以查看任何 item
    """
    item = await session.get(Item, id)
    if not item:
        raise_item_not_found()
    
    # 检查权限（所有者或 admin）
    await check_item_owner_or_admin(session, current_user, item.owner_id)
    
    return item


@router.post(
    "/",
    response_model=ItemPublic,
    dependencies=[Depends(require_scope(ItemScope.CREATE))],
)
async def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """
    Create new item.
    
    需要 item:create 权限。
    """
    item = Item.model_validate(item_in, update={"owner_id": current_user.id})
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.put(
    "/{id}",
    response_model=ItemPublic,
    dependencies=[Depends(require_any_scope(ItemScope.UPDATE, ItemScope.ADMIN))],
)
async def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item.
    
    - 普通用户只能更新自己的 item（需要 item:update 权限）
    - 拥有 item:admin 权限的用户可以更新任何 item
    """
    item = await session.get(Item, id)
    if not item:
        raise_item_not_found()
    
    # 检查权限（所有者或 admin）
    await check_item_owner_or_admin(session, current_user, item.owner_id)
    
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.delete(
    "/{id}",
    dependencies=[Depends(require_any_scope(ItemScope.DELETE, ItemScope.ADMIN))],
)
async def delete_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an item.
    
    - 普通用户只能删除自己的 item（需要 item:delete 权限）
    - 拥有 item:admin 权限的用户可以删除任何 item
    """
    item = await session.get(Item, id)
    if not item:
        raise_item_not_found()
    
    # 检查权限（所有者或 admin）
    await check_item_owner_or_admin(session, current_user, item.owner_id)
    
    await session.delete(item)
    await session.commit()
    return Message(message="Item deleted successfully")
