"""
工资服务层模块

封装工资公式计算和批量编排逻辑。
"""
import json
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User, UserRoleType, RuleCategory
from app.core.errors import BusinessException, ErrorCode
from app.domains.starpoint import repository as starpoint_repo
from app.domains.system_rule import repository as rule_repo
from app.domains.salary.schemas import (
    EngineerSalaryDetail,
    EngineerSalarySummary,
    PMSalaryDetail,
    PMSalarySummary,
    SalarySummary,
)
from app.domains.shared.queries import get_engineer_monthly_hours


# ====================== 默认工资配置 ======================
_DEFAULT_SALARY_CONFIG = {
    "min_salary": 5000,
}


async def _load_salary_config(session: AsyncSession) -> dict:
    """
    从 system_param 分类加载工资相关参数。
    """
    config = _DEFAULT_SALARY_CONFIG.copy()
    rules, _ = await rule_repo.get_rules(
        session=session,
        category=RuleCategory.SYSTEM_PARAM,
        skip=0,
        limit=100,
    )
    for rule in rules:
        if rule.is_active:
            try:
                values = json.loads(rule.value)
                config.update(values)
            except (json.JSONDecodeError, TypeError):
                continue
    return config


async def calculate_engineer_salary(
    *,
    session: AsyncSession,
    engineer: User,
    k_coefficient: float,
    month: Optional[str] = None,
) -> EngineerSalaryDetail:
    """
    计算工程师工资

    公式：S下 = max(5000, (S0 - P差额) × K)
    其中：
      H0 = S0 ÷ T月计划（自动计算，不再依赖管理员手动设置）
      P差额 = max(0, T月计划 - T有效) × H0（衡量"本月未完成的工时价值"）
      T有效 = 已完成任务 min(T实, T报) 之和（由工单 02 写入）
    """
    T_effective_total, T_reported_total = await get_engineer_monthly_hours(
        session=session,
        engineer_id=engineer.id,
        month=month,
    )

    S0 = engineer.S0 or 0.0
    T_monthly_plan = engineer.T_monthly_plan or 0.0

    # H0 = S0 ÷ T月计划（自动计算）
    H0 = S0 / T_monthly_plan if T_monthly_plan > 0 else 0.0

    # P差额 = max(0, T月计划 - T有效) × H0
    P_diff = max(0, T_monthly_plan - T_effective_total) * H0

    # 从数据库加载最低工资下限
    salary_config = await _load_salary_config(session)
    min_salary = salary_config.get("min_salary", 5000)

    # 最终工资 = max(min_salary, (S0 - P差额) × K)
    salary_final = max(min_salary, (S0 - P_diff) * k_coefficient)

    return EngineerSalaryDetail(
        user_id=engineer.id,
        full_name=engineer.full_name,
        role="engineer",
        S0=S0,
        H0=H0,
        T_monthly_plan=T_monthly_plan,
        T_actual_monthly=T_effective_total,
        T_reported_monthly=T_reported_total,
        T_effective=T_effective_total,
        P_diff=P_diff,
        current_starpoint=engineer.current_starpoint,
        k_coefficient=k_coefficient,
        salary_final=salary_final,
    )


async def calculate_engineer_salary_summary(
    *,
    session: AsyncSession,
    engineer: User,
    k_coefficient: float,
    month: Optional[str] = None,
) -> EngineerSalarySummary:
    """计算工程师工资，返回管理员汇总视图"""
    detail = await calculate_engineer_salary(
        session=session, engineer=engineer, k_coefficient=k_coefficient, month=month,
    )
    return EngineerSalarySummary(
        user_id=detail.user_id,
        full_name=detail.full_name,
        role="engineer",
        S0=detail.S0,
        H0=detail.H0,
        T_monthly_plan=detail.T_monthly_plan,
        T_effective=detail.T_effective,
        T_actual_monthly=detail.T_actual_monthly,
        T_reported_monthly=detail.T_reported_monthly,
        P_diff=detail.P_diff,
        k_coefficient=detail.k_coefficient,
        current_starpoint=detail.current_starpoint,
        salary_final=detail.salary_final,
    )


async def calculate_pm_salary(
    *,
    pm: User,
) -> PMSalaryDetail:
    """计算 PM 工资：S总 = S底 + S考"""
    S_base = pm.S_base or 0.0
    S_assess = pm.S_assess or 0.0
    salary_total = S_base + S_assess

    return PMSalaryDetail(
        user_id=pm.id,
        full_name=pm.full_name,
        role="pm",
        S_base=S_base,
        S_assess=S_assess,
        R_base=pm.R_base,
        R_assess=pm.R_assess,
        salary_total=salary_total,
    )


async def calculate_pm_salary_summary(
    *,
    pm: User,
) -> PMSalarySummary:
    """计算 PM 工资，返回管理员汇总视图"""
    detail = await calculate_pm_salary(pm=pm)
    return PMSalarySummary(
        user_id=detail.user_id,
        full_name=detail.full_name,
        role="pm",
        S_base=detail.S_base,
        S_assess=detail.S_assess,
        R_base=detail.R_base,
        R_assess=detail.R_assess,
        salary_total=detail.salary_total,
    )


async def calculate_user_salary(
    *,
    session: AsyncSession,
    user: User,
    month: Optional[str] = None,
) -> EngineerSalaryDetail | PMSalaryDetail:
    """计算单个用户工资（工程师或 PM）"""
    if user.role == UserRoleType.ENGINEER:
        k_coefficient = await starpoint_repo.calculate_k_coefficient(
            session=session,
            engineer_id=user.id,
        )
        return await calculate_engineer_salary(
            session=session,
            engineer=user,
            k_coefficient=k_coefficient,
            month=month,
        )
    elif user.role == UserRoleType.PM:
        return await calculate_pm_salary(pm=user)
    else:
        raise BusinessException(
            code=ErrorCode.USER_ROLE_MISMATCH,
            detail=f"User role {user.role} does not support salary calculation",
        )


async def calculate_all_salaries_detail(
    *,
    session: AsyncSession,
    users: list[User],
    month: Optional[str] = None,
) -> list[EngineerSalarySummary | PMSalarySummary]:
    """批量计算所有用户工资，返回明细汇总视图（用于管理员页面）"""
    result: list[EngineerSalarySummary | PMSalarySummary] = []

    for user in users:
        try:
            if user.role == UserRoleType.ENGINEER:
                k_coefficient = await starpoint_repo.calculate_k_coefficient(
                    session=session,
                    engineer_id=user.id,
                )
                summary = await calculate_engineer_salary_summary(
                    session=session, engineer=user, k_coefficient=k_coefficient, month=month,
                )
            elif user.role == UserRoleType.PM:
                summary = await calculate_pm_salary_summary(pm=user)
            else:
                continue
            result.append(summary)
        except BusinessException:
            continue

    return result


async def calculate_all_salaries(
    *,
    session: AsyncSession,
    users: list[User],
) -> tuple[list[SalarySummary], float, float, float]:
    """批量计算所有用户工资，返回汇总数据（旧版，供 dashboard 使用）"""
    salary_summaries: list[SalarySummary] = []
    engineer_cost = 0.0
    pm_cost = 0.0

    for user in users:
        try:
            calculated = await calculate_user_salary(session=session, user=user)
            if isinstance(calculated, EngineerSalaryDetail):
                salary = calculated.salary_final
                engineer_cost += salary
            else:
                salary = calculated.salary_total
                pm_cost += salary
        except BusinessException:
            salary = 0.0

        salary_summaries.append(SalarySummary(
            user_id=user.id,
            full_name=user.full_name,
            role=user.role.value,
            salary=salary,
        ))

    total_salary = engineer_cost + pm_cost
    return salary_summaries, total_salary, engineer_cost, pm_cost