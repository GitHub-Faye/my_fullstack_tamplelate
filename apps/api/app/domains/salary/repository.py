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
) -> dict:
    """
    计算工程师工资

    公式：S下 = (S0 - P差额) × K
    其中 P差额 = H0 × (T实际 - T报价)

    Args:
        session: 数据库会话
        engineer: 工程师用户对象
        k_coefficient: K 系数

    Returns:
        工资计算详情字典
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
    salary_final = (S0 - P_diff) * k_coefficient

    return {
        "user_id": engineer.id,
        "full_name": engineer.full_name,
        "role": "engineer",
        "S0": S0,
        "H0": H0,
        "T_monthly_plan": engineer.T_monthly_plan,
        "T_actual_monthly": T_actual,
        "T_reported_monthly": T_reported,
        "P_diff": P_diff,
        "current_starpoint": engineer.current_starpoint,
        "k_coefficient": k_coefficient,
        "salary_final": max(0, salary_final),  # 工资不能为负
    }


# ============================== PM 工资计算 ==============================

async def calculate_pm_salary(
    *,
    pm: User,
) -> dict:
    """
    计算 PM 工资

    公式：S总 = S底 + S考

    Args:
        pm: PM 用户对象

    Returns:
        工资计算详情字典
    """
    S_base = pm.S_base or 0.0
    S_assess = pm.S_assess or 0.0

    salary_total = S_base + S_assess

    return {
        "user_id": pm.id,
        "full_name": pm.full_name,
        "role": "pm",
        "S_base": S_base,
        "S_assess": S_assess,
        "R_base": pm.R_base,
        "R_assess": pm.R_assess,
        "salary_total": salary_total,
    }


# ============================== 工资汇总（管理员） ==============================

async def get_all_salaries(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[list[dict], int]:
    """
    获取所有员工的工资汇总

    Args:
        session: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数上限

    Returns:
        (工资列表, 总数) 元组
    """
    # 计数（工程师 + PM）
    count_stmt = select(func.count()).select_from(User).where(
        User.role.in_([UserRoleType.ENGINEER.value, UserRoleType.PM.value])
    )
    result = await session.execute(count_stmt)
    count = result.scalar_one()

    # 查询所有工程师和 PM
    stmt = (
        select(User)
        .where(User.role.in_([UserRoleType.ENGINEER.value, UserRoleType.PM.value]))
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    users = list(result.scalars().all())

    salaries = []
    for user in users:
        if user.role == UserRoleType.ENGINEER:
            # 工程师工资需要 K 系数，这里暂时用 1.0（实际调用时需要从星点模块获取）
            # 为了简化，这里先用简化逻辑，实际 API 中会调用星点模块
            S0 = user.S0 or 0.0
            # 简化，实际需要完整计算
            salary = S0
        else:  # PM
            salary = (user.S_base or 0.0) + (user.S_assess or 0.0)

        salaries.append({
            "user_id": user.id,
            "full_name": user.full_name,
            "role": user.role.value,
            "salary": salary,
        })

    return salaries, count


async def update_user_salary_params(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    params: dict,
) -> Optional[User]:
    """
    更新用户工资参数

    Args:
        session: 数据库会话
        user_id: 用户 ID
        params: 参数字典

    Returns:
        更新后的用户对象，或 None（用户不存在）
    """
    user = await session.get(User, user_id)
    if not user:
        return None

    # 更新字段
    for key, value in params.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
