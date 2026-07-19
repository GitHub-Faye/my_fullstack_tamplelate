"""
工资服务层模块

封装工资公式计算和批量编排逻辑。
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User, UserRoleType
from app.core.errors import BusinessException, ErrorCode
from app.domains.salary import repository as salary_repo
from app.domains.starpoint import repository as starpoint_repo
from app.domains.salary.schemas import (
    EngineerSalaryDetail,
    PMSalaryDetail,
    SalarySummary,
)
from app.domains.shared.queries import get_engineer_monthly_hours


async def calculate_engineer_salary(
    *,
    session: AsyncSession,
    engineer: User,
    k_coefficient: float,
) -> EngineerSalaryDetail:
    """
    计算工程师工资

    公式：S下 = (S0 - P差额) × K
    其中 P差额 = H0 × (T实际 - T报价)
    """
    T_actual, T_reported = await get_engineer_monthly_hours(
        session=session,
        engineer_id=engineer.id,
    )

    S0 = engineer.S0 or 0.0
    H0 = engineer.H0 or 0.0
    P_diff = H0 * (T_actual - T_reported)
    T_effective = T_actual
    salary_final = max(0, (S0 - P_diff) * k_coefficient)

    return EngineerSalaryDetail(
        user_id=engineer.id,
        full_name=engineer.full_name,
        role="engineer",
        S0=S0,
        H0=H0,
        T_monthly_plan=engineer.T_monthly_plan,
        T_actual_monthly=T_actual,
        T_reported_monthly=T_reported,
        T_effective=T_effective,
        P_diff=P_diff,
        current_starpoint=engineer.current_starpoint,
        k_coefficient=k_coefficient,
        salary_final=salary_final,
    )


async def calculate_pm_salary(
    *,
    session: AsyncSession,
    pm: User,
) -> PMSalaryDetail:
    """计算 PM 工资：S总 = S底 + S考"""
    S_base = pm.S_base or 0.0
    S_assess = pm.S_assess or 0.0
    salary_total = S_base + S_assess

    actual_total = await salary_repo.get_pm_monthly_client_actual(
        session=session,
        pm_id=pm.id,
    )
    baseline_count = pm.baseline_client_count or 0

    return PMSalaryDetail(
        user_id=pm.id,
        full_name=pm.full_name,
        role="pm",
        S_base=S_base,
        S_assess=S_assess,
        R_base=pm.R_base,
        R_assess=pm.R_assess,
        L_actual=actual_total,
        L_base=baseline_count,
        salary_total=salary_total,
    )


async def calculate_user_salary(
    *,
    session: AsyncSession,
    user: User,
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
        )
    elif user.role == UserRoleType.PM:
        return await calculate_pm_salary(session=session, pm=user)
    else:
        raise BusinessException(
            code=ErrorCode.USER_ROLE_MISMATCH,
            detail=f"User role {user.role} does not support salary calculation",
        )


async def calculate_all_salaries(
    *,
    session: AsyncSession,
    users: list[User],
) -> tuple[list[SalarySummary], float, float, float]:
    """批量计算所有用户工资，返回汇总数据"""
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