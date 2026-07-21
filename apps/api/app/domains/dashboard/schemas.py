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
    T_monthly_plan: float = Field(description="T月计划")
    T_actual_monthly: float = Field(description="T实（本月实际工时）")
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
    yesterday_new_clients: int = Field(description="昨日新增客资数（环比对照）")
    last_month_new_clients: int = Field(description="上月新增客资数（环比对照）")

    # 任务指标
    pm_task_count: int = Field(description="我发布的任务总数")
    task_count_unconfirmed: int = Field(description="未确认任务数")
    task_count_bidding: int = Field(description="竞价中任务数")
    task_count_in_progress: int = Field(description="进行中任务数")
    task_count_paused: int = Field(description="暂停中任务数")
    task_count_completed: int = Field(description="已完成任务数")

    # 收入指标
    salary_preview: float = Field(description="收入试算（元）")
    salary_detail_url: str = Field(default="", description="工资明细 URL（暂为空）")


# ==================== 管理员指标 ====================

class EngineerLoad(SQLModel):
    """工程师负载条目"""
    user_id: uuid.UUID
    full_name: Optional[str] = None
    current_tasks: int = Field(description="当前进行中任务数")
    T_actual_monthly: float = Field(description="T实（本月实际工时）")
    T_remaining: float = Field(description="本月剩余工时")
    accuracy_rate: float = Field(description="T报准确率（%）")


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
    total_salary: float = Field(description="月度总收入（元）")
    engineer_salary_cost: float = Field(description="工程师总成本（元）")
    pm_salary_cost: float = Field(description="PM 总成本（元）")
