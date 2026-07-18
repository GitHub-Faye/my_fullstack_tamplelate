"""
工资模块数据传输对象（DTO）定义

定义工资相关的 API 请求和响应模型。
"""

import uuid
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.schemas import PaginatedResponse


# ==================== API 请求模型 ====================

class SalaryParamsUpdate(SQLModel):
    """管理员设置工资参数请求"""
    # 工程师字段
    S0: Optional[float] = Field(default=None, ge=0, description="月度工资基数")
    H0: Optional[float] = Field(default=None, ge=0, description="基准时薪")
    T_monthly_plan: Optional[float] = Field(default=None, ge=0, description="月度计划工时")

    # PM 字段
    S_base: Optional[float] = Field(default=None, ge=0, description="底薪")
    S_assess: Optional[float] = Field(default=None, ge=0, description="考核部分")
    R_base: Optional[float] = Field(default=None, ge=0, le=1, description="底薪比例")
    R_assess: Optional[float] = Field(default=None, ge=0, le=1, description="考核比例")
    baseline_client_count: Optional[int] = Field(default=None, ge=0, description="基准客资数")


# ==================== API 响应模型 ====================

class EngineerSalaryDetail(SQLModel):
    """工程师工资试算详情"""
    user_id: uuid.UUID
    full_name: Optional[str] = None
    role: str = "engineer"

    # 工资参数
    S0: float = Field(description="月度工资基数")
    H0: Optional[float] = Field(default=None, description="基准时薪")
    T_monthly_plan: Optional[float] = Field(default=None, description="月度计划工时")

    # 计算字段
    T_actual_monthly: float = Field(default=0.0, description="本月实际工时")
    T_reported_monthly: float = Field(default=0.0, description="本月报价工时")
    P_diff: float = Field(default=0.0, description="工时差额（T实际 - T报价）")
    current_starpoint: int = Field(default=0, description="当前星点总数")
    k_coefficient: float = Field(default=1.0, description="K系数")

    # 最终工资
    salary_final: float = Field(description="最终工资 S下 = (S0 - P差额) × K")


class PMSalaryDetail(SQLModel):
    """PM 工资试算详情"""
    user_id: uuid.UUID
    full_name: Optional[str] = None
    role: str = "pm"

    # 工资参数
    S_base: float = Field(description="底薪")
    S_assess: float = Field(description="考核部分")
    R_base: Optional[float] = Field(default=None, description="底薪比例")
    R_assess: Optional[float] = Field(default=None, description="考核比例")

    # 最终工资
    salary_total: float = Field(description="总工资 S总 = S底 + S考")


class SalarySummary(SQLModel):
    """工资汇总条目（管理员查看）"""
    user_id: uuid.UUID
    full_name: Optional[str] = None
    role: str
    salary: float = Field(description="工资金额")


class SalarySummaryList(PaginatedResponse[SalarySummary]):
    """工资汇总列表"""
    pass


class SalaryExportRequest(SQLModel):
    """工资导出请求"""
    month: Optional[str] = Field(default=None, description="导出月份（YYYY-MM），默认当前月")


class SalaryExportResponse(SQLModel):
    """工资导出响应"""
    record_count: int = Field(description="记录数")
