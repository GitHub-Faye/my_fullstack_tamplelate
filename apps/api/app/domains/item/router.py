import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentActiveSuperuser,
    CurrentUser,
    SessionDep,
    require_scope,
    require_any_scope,
)
from app.core.scopes import ItemScope
from app.core.schemas import Message, PaginationParams
from app.core.errors import raise_item_not_found

from app.domains.item import repository
from app.domains.item.schemas import (
    ItemCreate,
    ItemPublic,
    ItemsPublic,
    ItemUpdate,
)
from app.domains.item.dependencies import check_item_owner_or_admin

router = APIRouter()


@router.get(
    "/",
    response_model=ItemsPublic,
    dependencies=[Depends(require_any_scope(ItemScope.READ, ItemScope.ADMIN))],
)
async def read_items(
    session: SessionDep,
    current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Query()],
) -> Any:
    """
    Retrieve items.
    
    - Regular users can only view their own items
    - Users with item:admin permission can view all items
    """
    is_admin = current_user.is_superuser
    
    if is_admin:
        items, count = await repository.get_items(
            session=session,
            skip=pagination.offset,
            limit=pagination.limit,
        )
    else:
        items, count = await repository.get_items(
            session=session,
            owner_id=current_user.id,
            skip=pagination.offset,
            limit=pagination.limit,
        )
    
    return ItemsPublic(
        data=items,
        count=count,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(count + pagination.page_size - 1) // pagination.page_size if count > 0 else 0,
    )


@router.get(
    "/{item_id}",
    response_model=ItemPublic,
    dependencies=[Depends(require_any_scope(ItemScope.READ, ItemScope.ADMIN))],
)
async def read_item(
    session: SessionDep,
    current_user: CurrentUser,
    item_id: uuid.UUID,
) -> Any:
    """
    Get item by ID.
    
    - Regular users can only view their own items
    - Users with item:admin permission can view any item
    """
    item = await repository.get_item(session=session, item_id=item_id)
    if not item:
        raise_item_not_found()
    
    # Check permission (owner or admin)
    await check_item_owner_or_admin(session, current_user, item.owner_id)
    
    return item


@router.post(
    "/",
    response_model=ItemPublic,
    dependencies=[Depends(require_scope(ItemScope.CREATE))],
)
async def create_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    item_in: ItemCreate,
) -> Any:
    """
    Create new item.
    
    Requires item:create permission.
    """
    item = await repository.create_item(
        session=session,
        item_in=item_in,
        owner_id=current_user.id,
    )
    return item


@router.put(
    "/{item_id}",
    response_model=ItemPublic,
    dependencies=[Depends(require_any_scope(ItemScope.UPDATE, ItemScope.ADMIN))],
)
async def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    item_id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item.
    
    - Regular users can only update their own items (requires item:update permission)
    - Users with item:admin permission can update any item
    """
    item = await repository.get_item(session=session, item_id=item_id)
    if not item:
        raise_item_not_found()
    
    # Check permission (owner or admin)
    await check_item_owner_or_admin(session, current_user, item.owner_id)
    
    item = await repository.update_item(
        session=session,
        db_item=item,
        item_in=item_in,
    )
    return item


@router.delete("/{item_id}")
async def delete_item(
    session: SessionDep,
    current_user: CurrentActiveSuperuser,
    item_id: uuid.UUID,
) -> Message:
    """
    Delete an item.
    
    - Regular users can only delete their own items (requires item:delete permission)
    - Users with item:admin permission can delete any item
    """
    item = await repository.get_item(session=session, item_id=item_id)
    if not item:
        raise_item_not_found()
    
    # Check permission (owner or admin)
    await check_item_owner_or_admin(session, current_user, item.owner_id)
    
    await repository.delete_item(session=session, db_item=item)
    return Message(message="Item deleted successfully")
