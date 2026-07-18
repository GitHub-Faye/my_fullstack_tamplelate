"""
星点模块数据传输对象（DTO）定义

定义星点相关的 API 请求和响应模型。
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.models import JudgmentType
from app.core.schemas import PaginatedResponse


# ==================== API 请求模型 ====================

class StarPointAdjustRequest(SQLModel):
    """管理员手动调整星点请求"""
    engineer_id: uuid.UUID = Field(description="目标工程师ID")
    change_amount: int = Field(description="星点变化量（可正可负）")
    reason: Optional[str] = Field(default=None, max_length=500, description="调整原因")


# ==================== API 响应模型 ====================

class StarPointRecordPublic(SQLModel):
    """返回给客户端的星点记录"""
    id: uuid.UUID
    engineer_id: uuid.UUID
    task_id: Optional[uuid.UUID] = None
    change_amount: int
    reason: Optional[str] = None
    judgment_type: JudgmentType
    T_reported: Optional[float] = None
    T_actual: Optional[float] = None
    created_at: Optional[datetime] = None


class StarPointRecordsPublic(PaginatedResponse[StarPointRecordPublic]):
    """星点记录分页响应"""
    pass


class StarPointSummary(SQLModel):
    """星点汇总信息"""
    total_starpoints: int = Field(description="星点总数")
    current_month_earned: int = Field(description="本月获得星点")
    rank: Optional[int] = Field(default=None, description="当前排名")
    k_coefficient: float = Field(default=1.0, description="K系数")


class StarPointLeaderboardEntry(SQLModel):
    """排行榜条目"""
    engineer_id: uuid.UUID
    engineer_name: Optional[str] = None
    total_starpoints: int
    rank: int
    k_coefficient: float


class StarPointLeaderboard(SQLModel):
    """排行榜响应"""
    data: list[StarPointLeaderboardEntry]
    count: int
