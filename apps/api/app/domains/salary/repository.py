"""
工资模块数据访问层（Repository）

负责工资相关的数据库操作：查询用户工资参数、计算工资等。
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import func, select, and_, literal
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User, Task, TaskStatus, UserRoleType
from app.domains.salary.schemas import (
    SalaryParamsUpdate,
    EngineerSalaryDetail,
    PMSalaryDetail,
)


# ============================== 工程师工资计算 ==============================

async def get_engineer_monthly_hours(
    *,
    session: AsyncSession,
    engineer_id: uuid.UUID,
) -> Tuple[float, float]:
    """
    获取工程师本月实际工时和报价工时

    Args:
        session: 数据库会话
        engineer_id: 工程师 ID

    Returns:
        (T_actual_total, T_reported_total) 元组
    """
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stmt = (
        select(
            func.coalesce(func.sum(Task.T_actual), 0).label("T_actual_total"),
            func.coalesce(func.sum(Task.T_reported), 0).label("T_reported_total"),
        )
        .where(
            and_(
                Task.engineer_id == engineer_id,  # type: ignore[arg-type]
                Task.status == TaskStatus.COMPLETED,  # type: ignore[arg-type]
                Task.updated_at >= month_start,  # type: ignore[arg-type]
            )
        )
    )
    result = await session.execute(stmt)
    row = result.one()

    return float(row.T_actual_total or 0), float(row.T_reported_total or 0)


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

    Args:
        session: 数据库会话
        engineer: 工程师用户对象
        k_coefficient: K 系数

    Returns:
        EngineerSalaryDetail DTO
    """
    # 获取本月工时
    T_actual, T_reported = await get_engineer_monthly_hours(
        session=session,
        engineer_id=engineer.id,
    )

    # 工资参数（默认值保护）
    S0 = engineer.S0 or 0.0
    H0 = engineer.H0 or 0.0

    # 计算工时差额
    P_diff = H0 * (T_actual - T_reported)

    # 最终工资
    salary_final = max(0, (S0 - P_diff) * k_coefficient)  # 工资不能为负

    return EngineerSalaryDetail(
        user_id=engineer.id,
        full_name=engineer.full_name,
        role="engineer",
        S0=S0,
        H0=H0,
        T_monthly_plan=engineer.T_monthly_plan,
        T_actual_monthly=T_actual,
        T_reported_monthly=T_reported,
        P_diff=P_diff,
        current_starpoint=engineer.current_starpoint,
        k_coefficient=k_coefficient,
        salary_final=salary_final,
    )


# ============================== PM 工资计算 ==============================

async def calculate_pm_salary(
    *,
    pm: User,
) -> PMSalaryDetail:
    """
    计算 PM 工资

    公式：S总 = S底 + S考

    Args:
        pm: PM 用户对象

    Returns:
        PMSalaryDetail DTO（不需要 session，仅使用 User 字段）
    """
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


# ============================== 工资汇总（管理员） ==============================

_SALARY_USER_FILTER = User.role.in_([UserRoleType.ENGINEER.value, UserRoleType.PM.value])


async def get_all_salaries(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[list[User], int]:
    """
    获取所有工程师和 PM 用户列表

    Args:
        session: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数上限

    Returns:
        (用户列表, 总数) 元组
    """
    # 计数（工程师 + PM）
    count_stmt = select(func.count()).select_from(User).where(_SALARY_USER_FILTER)
    result = await session.execute(count_stmt)
    count = result.scalar_one()

    # 查询所有工程师和 PM
    stmt = (
        select(User)
        .where(_SALARY_USER_FILTER)
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    users = list(result.scalars().all())

    return users, count


async def update_user_salary_params(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    params: SalaryParamsUpdate,
) -> Optional[User]:
    """
    更新用户工资参数

    根据用户角色，仅更新该角色对应的字段：
    - 工程师：S0, H0, T_monthly_plan
    - PM：S_base, S_assess, R_base, R_assess, baseline_client_count

    Args:
        session: 数据库会话
        user_id: 用户 ID
        params: SalaryParamsUpdate DTO

    Returns:
        更新后的用户对象，或 None（用户不存在）
    """
    user = await session.get(User, user_id)
    if not user:
        return None

    # 按角色更新对应字段
    if user.role == UserRoleType.ENGINEER:
        if params.S0 is not None:
            user.S0 = params.S0
        if params.H0 is not None:
            user.H0 = params.H0
        if params.T_monthly_plan is not None:
            user.T_monthly_plan = params.T_monthly_plan
    elif user.role == UserRoleType.PM:
        if params.S_base is not None:
            user.S_base = params.S_base
        if params.S_assess is not None:
            user.S_assess = params.S_assess
        if params.R_base is not None:
            user.R_base = params.R_base
        if params.R_assess is not None:
            user.R_assess = params.R_assess
        if params.baseline_client_count is not None:
            user.baseline_client_count = params.baseline_client_count

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
