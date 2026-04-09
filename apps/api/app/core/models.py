# app/core/models.py   （或你当前的文件）

import uuid
from datetime import datetime, timezone
from typing import List, Optional   # 保留 typing.List

from pydantic import EmailStr
from sqlalchemy import DateTime, ForeignKey
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    """返回 UTC 时间，用于默认 created_at 字段。"""
    return datetime.now(timezone.utc)


# ==================================== UserRole (Association Table) ====================================
# 必须在 Role 和 User 之前定义，因为它们都引用了这个类

class UserRole(SQLModel, table=True):
    """用户与角色的多对多关联表"""
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    role_id: uuid.UUID = Field(
        foreign_key="role.id",
        primary_key=True,
        ondelete="CASCADE",
    )


# ==================================== Role ====================================

class RoleBase(SQLModel):
    name: str = Field(unique=True, index=True, max_length=50)


class Role(RoleBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # 与 User 的多对多关系（通过 UserRole 关联表）
    users: List["User"] = Relationship(
        back_populates="roles",
        link_model=UserRole,
    )
    # 与 RoleScope 的一对多关系
    scopes: List["RoleScope"] = Relationship(
        back_populates="role",
        cascade_delete=True,
    )


# ==================================== RoleScope ====================================

class RoleScopeBase(SQLModel):
    scope: str = Field(max_length=100)  # 如 "item:read", "item:create"


class RoleScope(RoleScopeBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    role_id: uuid.UUID = Field(
        foreign_key="role.id", nullable=False, ondelete="CASCADE"
    )
    created_at: Optional[datetime] = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # 与 Role 的多对一关系
    role: Optional["Role"] = Relationship(back_populates="scopes")


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

    # 与 Item 的一对多关系
    items: List["Item"] = Relationship(
        back_populates="owner",
        cascade_delete=True,          # 推荐，替代 cascade="all, delete-orphan"
    )
    # 与 Role 的多对多关系（通过 UserRole 关联表）
    roles: List["Role"] = Relationship(
        back_populates="users",
        link_model=UserRole,
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
