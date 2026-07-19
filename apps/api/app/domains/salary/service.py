"""
工资服务层模块

封装跨域批量工资计算逻辑，供 salary 路由和 dashboard 路由统一调用。
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


async def calculate_user_salary(
    *,
    session: AsyncSession,
    user: User,
) -> EngineerSalaryDetail | PMSalaryDetail:
    """
    计算单个用户工资（工程师或 PM）

    Args:
        session: 数据库会话
        user: 用户对象

    Returns:
        EngineerSalaryDetail 或 PMSalaryDetail 的 DTO 实例

    Raises:
        BusinessException: 用户角色不支持工资计算
    """
    if user.role == UserRoleType.ENGINEER:
        k_coefficient = await starpoint_repo.calculate_k_coefficient(
            session=session,
            engineer_id=user.id,
        )
        return await salary_repo.calculate_engineer_salary(
            session=session,
            engineer=user,
            k_coefficient=k_coefficient,
        )
    elif user.role == UserRoleType.PM:
        return await salary_repo.calculate_pm_salary(pm=user)
    else:
        raise BusinessException(
            code=ErrorCode.USER_ROLE_MISMATCH,
            detail=f"User role {user.role} does not support salary calculation"
        )


async def calculate_all_salaries(
    *,
    session: AsyncSession,
    users: list[User],
) -> tuple[list[SalarySummary], float, float, float]:
    """
    批量计算所有用户工资，返回汇总数据和聚合金额。

    Args:
        session: 数据库会话
        users: 用户列表（工程师和 PM）

    Returns:
        (salary_summaries, total_salary, engineer_cost, pm_cost) 元组
    """
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