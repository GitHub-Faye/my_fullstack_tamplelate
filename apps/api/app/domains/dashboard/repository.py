"""
数据概览模块数据访问层（Repository）

负责 Dashboard 相关的数据库操作：统计查询、聚合计算等。
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    User,
    Task,
    TaskStatus,
    UserRoleType,
    DailyReport,
    ClientResource,
)
from app.domains.dashboard.schemas import (
    EngineerDashboard,
    PMDashboard,
    AdminDashboard,
    EngineerLoad,
    StarpointRank,
)


async def get_engineer_dashboard(
    *,
    session: AsyncSession,
    engineer: User,
    salary_preview: float,
) -> EngineerDashboard:
    """
    获取工程师仪表板数据

    Args:
        session: 数据库会话
        engineer: 工程师用户对象
        salary_preview: 收入试算（由调用方计算）

    Returns:
        EngineerDashboard DTO
    """
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 本月实际工时（已完成任务）
    stmt = (
        select(func.coalesce(func.sum(Task.T_actual), 0))
        .where(
            and_(
                Task.engineer_id == engineer.id,
                Task.status == TaskStatus.COMPLETED,
                Task.updated_at >= month_start,
            )
        )
    )
    result = await session.execute(stmt)
    T_actual_monthly = float(result.scalar_one() or 0)

    # T报准确率：本月已完成任务的 T_actual / T_reported 比值
    accuracy_stmt = (
        select(
            func.coalesce(func.sum(Task.T_actual), 0),
            func.coalesce(func.sum(Task.T_reported), 0),
        )
        .where(
            and_(
                Task.engineer_id == engineer.id,
                Task.status == TaskStatus.COMPLETED,
                Task.updated_at >= month_start,
                Task.T_reported > 0,
            )
        )
    )
    result = await session.execute(accuracy_stmt)
    row = result.one()
    T_actual_sum = float(row[0] or 0)
    T_reported_sum = float(row[1] or 0)
    accuracy_rate = (T_actual_sum / T_reported_sum * 100) if T_reported_sum > 0 else 100.0

    # 剩余工时 = 月度计划 - 本月实际
    T_monthly_plan = engineer.T_monthly_plan or 0.0
    T_remaining = max(0, T_monthly_plan - T_actual_monthly)

    return EngineerDashboard(
        user_id=engineer.id,
        full_name=engineer.full_name,
        current_starpoint=engineer.current_starpoint or 0,
        T_monthly_plan=T_monthly_plan,
        T_actual_monthly=T_actual_monthly,
        T_remaining=T_remaining,
        salary_preview=salary_preview,
        accuracy_rate=round(accuracy_rate, 2),
    )


async def get_pm_dashboard(
    *,
    session: AsyncSession,
    pm: User,
    salary_preview: float,
) -> PMDashboard:
    """
    获取 PM 仪表板数据

    Args:
        session: 数据库会话
        pm: PM 用户对象
        salary_preview: 收入试算（由调用方计算）

    Returns:
        PMDashboard DTO
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 今日新增客资
    today_stmt = select(func.count()).select_from(ClientResource).where(
        and_(
            ClientResource.pm_id == pm.id,
            ClientResource.created_at >= today_start,
        )
    )
    result = await session.execute(today_stmt)
    today_new_clients = result.scalar_one() or 0

    # 本月新增客资
    monthly_stmt = select(func.count()).select_from(ClientResource).where(
        and_(
            ClientResource.pm_id == pm.id,
            ClientResource.created_at >= month_start,
        )
    )
    result = await session.execute(monthly_stmt)
    monthly_new_clients = result.scalar_one() or 0

    return PMDashboard(
        user_id=pm.id,
        full_name=pm.full_name,
        today_new_clients=today_new_clients,
        monthly_new_clients=monthly_new_clients,
        salary_preview=salary_preview,
    )


async def get_admin_dashboard(
    *,
    session: AsyncSession,
) -> AdminDashboard:
    """
    获取管理员仪表板数据

    Args:
        session: 数据库会话

    Returns:
        AdminDashboard DTO
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 今日新增客资
    today_clients_stmt = select(func.count()).select_from(ClientResource).where(
        ClientResource.created_at >= today_start
    )
    result = await session.execute(today_clients_stmt)
    today_new_clients = result.scalar_one() or 0

    # 本月新增客资
    monthly_clients_stmt = select(func.count()).select_from(ClientResource).where(
        ClientResource.created_at >= month_start
    )
    result = await session.execute(monthly_clients_stmt)
    monthly_new_clients = result.scalar_one() or 0

    # 今日提交日志量
    today_reports_stmt = select(func.count()).select_from(DailyReport).where(
        DailyReport.created_at >= today_start
    )
    result = await session.execute(today_reports_stmt)
    today_submitted_reports = result.scalar_one() or 0

    # 进行中任务数
    ongoing_stmt = select(func.count()).select_from(Task).where(
        Task.status == TaskStatus.IN_PROGRESS
    )
    result = await session.execute(ongoing_stmt)
    ongoing_tasks = result.scalar_one() or 0

    # 工程师负载：每个工程师的进行中任务数 + 本月实际工时
    month_start_for_tasks = month_start
    engineer_load_stmt = (
        select(
            User.id,
            User.full_name,
            func.count(Task.id).filter(Task.status == TaskStatus.IN_PROGRESS).label("ongoing_tasks"),
            func.coalesce(func.sum(Task.T_actual).filter(
                and_(
                    Task.status == TaskStatus.COMPLETED,
                    Task.updated_at >= month_start_for_tasks,
                )
            ), 0).label("T_actual_monthly"),
        )
        .select_from(User)
        .outerjoin(Task, Task.engineer_id == User.id)
        .where(User.role == UserRoleType.ENGINEER)
        .group_by(User.id)
    )
    result = await session.execute(engineer_load_stmt)
    engineer_loads = [
        EngineerLoad(
            user_id=row.id,
            full_name=row.full_name,
            current_tasks=row.ongoing_tasks or 0,
            T_actual_monthly=float(row.T_actual_monthly or 0),
        )
        for row in result.all()
    ]

    # 星点排行榜 Top 10
    starpoint_stmt = (
        select(User.id, User.full_name, User.current_starpoint)
        .where(User.role == UserRoleType.ENGINEER)
        .order_by(User.current_starpoint.desc())
        .limit(10)
    )
    result = await session.execute(starpoint_stmt)
    starpoint_ranks = [
        StarpointRank(
            user_id=row.id,
            full_name=row.full_name,
            current_starpoint=row.current_starpoint or 0,
        )
        for row in result.all()
    ]

    # 收入统计：所有工程师和 PM 的工资总和（简化计算）
    # 使用工资参数估算，不调用完整工资计算
    engineer_salary_stmt = select(func.coalesce(func.sum(User.S0), 0)).where(
        User.role == UserRoleType.ENGINEER
    )
    result = await session.execute(engineer_salary_stmt)
    engineer_salary_sum = float(result.scalar_one() or 0)

    pm_salary_stmt = select(
        func.coalesce(func.sum(User.S_base), 0) + func.coalesce(func.sum(User.S_assess), 0)
    ).where(User.role == UserRoleType.PM)
    result = await session.execute(pm_salary_stmt)
    pm_salary_sum = float(result.scalar_one() or 0)

    total_salary = engineer_salary_sum + pm_salary_sum

    return AdminDashboard(
        today_new_clients=today_new_clients,
        monthly_new_clients=monthly_new_clients,
        today_submitted_reports=today_submitted_reports,
        ongoing_tasks=ongoing_tasks,
        engineer_loads=engineer_loads,
        starpoint_ranks=starpoint_ranks,
        total_salary=total_salary,
    )
