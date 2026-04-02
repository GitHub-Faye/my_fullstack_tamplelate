# app/core/models.py   （或你当前的文件）

import uuid
from datetime import datetime, timezone
from typing import List, Optional   # 保留 typing.List

from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    """返回 UTC 时间，用于默认 created_at 字段。"""
    return datetime.now(timezone.utc)


# ==================================== User ====================================
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = Field(default=None, max_length=255)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # 关键修改在这里
    items: List["Item"] = Relationship(
        back_populates="owner",
        cascade_delete=True,          # 推荐，替代 cascade="all, delete-orphan"
    )


# ==================================== Item ====================================
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=255)


class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )

    # 关键修改在这里
    owner: Optional["User"] = Relationship(back_populates="items")