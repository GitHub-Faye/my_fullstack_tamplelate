"""
日报模块数据传输对象（DTO）定义

定义日报相关的 API 请求和响应模型。
"""

import uuid
from datetime import datetime, date
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.models import ReportStage
from app.core.schemas import PaginatedResponse


# ==================== 日报基础模型 ====================

class DailyReportBase(SQLModel):
    """日报基础属性"""
    today_hours: float = Field(ge=0, description="今日工作时长（小时）")
    current_stage: ReportStage = Field(description="当前阶段")
    progress: Optional[str] = Field(default=None, max_length=500, description="进度描述")
    completion_judgment: Optional[str] = Field(default=None, max_length=500, description="完成判定说明")
    starpoint_change: Optional[int] = Field(default=0, description="星点变化量")
    notes: Optional[str] = Field(default=None, max_length=1000, description="备注说明")
    summary: Optional[str] = Field(default=None, max_length=1000, description="工作总结")
    has_blocker: bool = Field(default=False, description="是否有阻塞问题")


# ==================== API 请求模型（Request DTO） ====================

class DailyReportCreate(DailyReportBase):
    """创建日报请求"""
    task_id: uuid.UUID = Field(description="关联任务ID")
    report_date: Optional[date] = Field(default=None, description="报告日期（默认今天）")


class DailyReportUpdate(SQLModel):
    """更新日报请求"""
    today_hours: Optional[float] = Field(default=None, ge=0, description="今日工作时长（小时）")
    current_stage: Optional[ReportStage] = Field(default=None, description="当前阶段")
    progress: Optional[str] = Field(default=None, max_length=500, description="进度描述")
    completion_judgment: Optional[str] = Field(default=None, max_length=500, description="完成判定说明")
    starpoint_change: Optional[int] = Field(default=None, description="星点变化量")
    notes: Optional[str] = Field(default=None, max_length=1000, description="备注说明")
    summary: Optional[str] = Field(default=None, max_length=1000, description="工作总结")
    has_blocker: Optional[bool] = Field(default=None, description="是否有阻塞问题")


# ==================== API 响应模型（Response DTO） ====================

class DailyReportPublic(DailyReportBase):
    """返回给客户端的日报信息"""
    id: uuid.UUID
    engineer_id: uuid.UUID
    task_id: uuid.UUID
    report_date: datetime
    created_at: Optional[datetime] = None


class DailyReportsPublic(PaginatedResponse[DailyReportPublic]):
    """日报列表分页响应"""
    pass


class DailyReportWithTaskName(DailyReportPublic):
    """日报响应（含任务名称及任务的 T报/T实）"""
    task_name: Optional[str] = Field(default=None, description="任务名称")
    T_reported: Optional[float] = Field(default=None, ge=0, description="T报（工程师报价工时）")
    T_actual: Optional[float] = Field(default=None, ge=0, description="T实（实际结算工时）")


class DailyReportsWithTaskNamePublic(SQLModel):
    """日报列表分页响应（含任务名称及 T报/T实）"""
    data: list[DailyReportWithTaskName]
    count: int
    page: int | None = None
    page_size: int | None = None
    total_pages: int | None = None


# ==================== 提醒模型 ====================

class RemindResult(SQLModel):
    """提醒未提交日报结果"""
    total_engineers: int = Field(description="工程师总数")
    submitted_today: int = Field(description="今日已提交日报人数")
    not_submitted: int = Field(description="未提交人数")
    not_submitted_engineers: list[str] = Field(default_factory=list, description="未提交日报的工程师姓名列表")