import uuid
from typing import Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Item
from app.domains.item.schemas import ItemCreate, ItemUpdate

# ============================== Item CRUD Operations ==============================

async def get_item(*, session: AsyncSession, item_id: uuid.UUID) -> Item | None:
    """
    Get item by ID.
    
    Args:
        session: Database session
        item_id: Item UUID
        
    Returns:
        Item object or None if not found
    """
    return await session.get(Item, item_id)


async def get_items(
    *,
    session: AsyncSession,
    owner_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[list[Item], int]:
    """
    Get paginated items list with optional owner filter.
    
    Args:
        session: Database session
        owner_id: Filter by owner ID (None for all items)
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        Tuple of (items list, total count)
    """
    # Build count query
    count_statement = select(func.count()).select_from(Item)
    if owner_id:
        count_statement = count_statement.where(Item.owner_id == owner_id)
    
    result = await session.execute(count_statement)
    count = result.scalar_one()
    
    # Build items query
    statement = select(Item).order_by(Item.created_at.desc())
    if owner_id:
        statement = statement.where(Item.owner_id == owner_id)
    
    statement = statement.offset(skip).limit(limit)
    result = await session.execute(statement)
    items = result.scalars().all()
    
    return list(items), count


async def create_item(
    *,
    session: AsyncSession,
    item_in: ItemCreate,
    owner_id: uuid.UUID,
) -> Item:
    """
    Create new item.
    
    Args:
        session: Database session
        item_in: Item creation data
        owner_id: Owner user ID
        
    Returns:
        Created item object
    """
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item


async def update_item(
    *,
    session: AsyncSession,
    db_item: Item,
    item_in: ItemUpdate,
) -> Item:
    """
    Update existing item.
    
    Args:
        session: Database session
        db_item: Existing item database object
        item_in: Item update data
        
    Returns:
        Updated item object
    """
    update_data = item_in.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(update_data)
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item


async def delete_item(*, session: AsyncSession, db_item: Item) -> None:
    """
    Delete item.
    
    Args:
        session: Database session
        db_item: Item database object to delete
    """
    await session.delete(db_item)
    await session.commit()


async def count_items_by_owner(*, session: AsyncSession, owner_id: uuid.UUID) -> int:
    """
    Count items owned by specific user.
    
    Args:
        session: Database session
        owner_id: Owner user ID
        
    Returns:
        Number of items owned by the user
    """
    statement = select(func.count()).select_from(Item).where(Item.owner_id == owner_id)
    result = await session.execute(statement)
    return result.scalar_one()
