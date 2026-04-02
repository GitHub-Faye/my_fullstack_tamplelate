import uuid
from typing import Any

from sqlmodel import Session
from models import Item, ItemCreate

# ============================== 物品 CRUD 操作 ==============================

def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    """
    创建物品。
    - 将请求 DTO (ItemCreate) 转换为数据库模型 (Item)
    - 自动关联到指定的 owner_id
    - 插入数据库并返回完整的物品对象
    """
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

