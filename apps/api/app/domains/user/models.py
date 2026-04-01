from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, func


class User(SQLModel, table=True):
    """用户数据库模型"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    username: str = Field(index=True, unique=True, max_length=50)
    email: Optional[str] = Field(default=None, index=True, unique=True, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=100)
    hashed_password: str = Field(max_length=255)
    disabled: bool = Field(default=False)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
