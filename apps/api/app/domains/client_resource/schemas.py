"""
客资管理模块数据传输对象（DTO）定义

定义客资相关的 API 请求和响应模型。
"""

import uuid
from datetime import datetime
from typing import Optional

from datetime import datetime, date

from sqlmodel import Field, SQLModel

from app.core.schemas import PaginatedResponse


# ==================== API 请求模型 ====================

class ClientResourceCreate(SQLModel):
    """录入客资请求"""
    actual_count: int = Field(ge=0, description="实际客资数")
    date: str = Field(description="记录日期（ISO 格式，如 2026-07-18）")


# ==================== API 响应模型 ====================

class ClientResourcePublic(SQLModel):
    """客资公开信息"""
    id: uuid.UUID
    pm_id: uuid.UUID
    actual_count: int
    baseline_count: int
    date: datetime
    created_at: Optional[datetime] = None


class ClientResourcesPublic(PaginatedResponse[ClientResourcePublic]):
    """客资列表"""
    pass


class ClientResourceSummary(SQLModel):
    """PM 客资汇总（管理员视角）"""
    pm_id: uuid.UUID
    pm_name: str
    baseline_count: int | None = None
    total_actual: int = 0
    avg_actual: float = 0.0
    record_count: int = 0
    performance_rate: float | None = None  # (total_actual - baseline * record_count) / (baseline * record_count)