"""
竞价模块 — Schema 定义

提供竞价报价和结算相关的 DTO。
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class BidCreate(SQLModel):
    """创建竞价报价请求"""
    T_reported: float = Field(ge=0, description="工程师报价工时")


class BidUpdate(SQLModel):
    """修改竞价报价请求"""
    T_reported: float = Field(ge=0, description="工程师报价工时")


class BidPublic(SQLModel):
    """返回给客户端的竞价报价信息"""
    id: uuid.UUID
    task_id: uuid.UUID
    engineer_id: uuid.UUID
    T_reported: float
    amount: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BidsPublic(SQLModel):
    """竞价报价列表响应"""
    data: list[BidPublic]
    count: int