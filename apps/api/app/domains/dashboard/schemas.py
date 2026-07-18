"""
数据概览模块数据传输对象（DTO）定义

定义 Dashboard API 的请求和响应模型。
"""

import uuid
from typing import Optional

from sqlmodel import Field, SQLModel


# ==================== 工程师指标 ====================

class EngineerDashboard(SQLModel):
    """工程师工作台首页指标"""
    user_id: uuid.UUID
    full_name: Optional[str] = None

    # 星点指标
    current_starpoint: int = Field(description="当前星点总数")

    # 工时指标
    T_monthly_plan: float = Field(description="月度计划工时")
    T_actual_monthly: float = Field(description="本月实际工时")
    T_remaining: float = Field(description="本月剩余工时")

    # 收入指标
    salary_preview: float = Field(description="收入试算（元）")

    # 准确率
    accuracy_rate: float = Field(description="T报准确率（%）")


# ==================== PM 指标 ====================

class PMDashboard(SQLModel):
    """PM 工作台首页指标"""
    user_id: uuid.UUID
    full_name: Optional[str] = None

    # 客资指标
    today_new_clients: int = Field(description="今日新增客资数")
    monthly_new_clients: int = Field(description="本月新增客资数")

    # 收入指标
    salary_preview: float = Field(description="收入试算（元）")


# ==================== 管理员指标 ====================

class EngineerLoad(SQLModel):
    """工程师负载条目"""
    user_id: uuid.UUID
    full_name: Optional[str] = None
    current_tasks: int = Field(description="当前进行中任务数")
    T_actual_monthly: float = Field(description="本月实际工时")


class StarpointRank(SQLModel):
    """星点排行榜条目"""
    user_id: uuid.UUID
    full_name: Optional[str] = None
    current_starpoint: int = Field(description="当前星点总数")


class AdminDashboard(SQLModel):
    """管理端数据概览"""
    # 客资指标
    today_new_clients: int = Field(description="今日新增客资数")
    monthly_new_clients: int = Field(description="本月新增客资数")

    # 提交日志指标
    today_submitted_reports: int = Field(description="今日提交日志量")

    # 任务指标
    ongoing_tasks: int = Field(description="进行中任务数")

    # 工程师负载
    engineer_loads: list[EngineerLoad] = Field(default_factory=list, description="工程师负载列表")

    # 星点排行榜
    starpoint_ranks: list[StarpointRank] = Field(default_factory=list, description="星点排行榜（Top 10）")

    # 收入统计
    total_salary: float = Field(description="总收入统计（元）")
