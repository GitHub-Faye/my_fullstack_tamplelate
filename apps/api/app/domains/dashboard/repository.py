"""
数据概览模块数据访问层（Repository）

负责 Dashboard 相关的数据库操作：统计查询、聚合计算等。
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

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
from app.domains.task.repository import get_ongoing_task_count
from app.domains.starpoint.repository import get_leaderboard
from app.domains.shared.queries import get_engineer_monthly_hours, get_engineer_loads


def _get_time_bounds() -> Tuple[datetime, datetime, datetime]:
    """获取当前时间相关的裁剪时间：now, today_start, month_start"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return now, today_start, month_start


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
    _, _, month_start = _get_time_bounds()

    # 本月实际工时 + T报准确率（共享查询）
    T_actual_monthly, T_reported_monthly = await get_engineer_monthly_hours(
        session=session,
        engineer_id=engineer.id,
    )

    if T_reported_monthly > 0:
        accuracy_rate = min(T_actual_monthly / T_reported_monthly * 100, 100.0)
    else:
        accuracy_rate = 100.0

    # 剩余工时 = 月度计划 - 本月实际
    T_monthly_plan = engineer.T_monthly_plan or 0.0
    T_remaining = max(0, T_monthly_plan - T_actual_monthly)

    # 进行中任务数
    in_progress_stmt = select(func.count()).select_from(Task).where(
        Task.engineer_id == engineer.id,
        Task.status == TaskStatus.IN_PROGRESS,
    )
    result = await session.execute(in_progress_stmt)
    in_progress_task_count = result.scalar_one() or 0

    return EngineerDashboard(
        user_id=engineer.id,
        full_name=engineer.full_name,
        current_starpoint=engineer.current_starpoint or 0,
        in_progress_task_count=in_progress_task_count,
        T_monthly_plan=T_monthly_plan,
        T_actual_monthly=T_actual_monthly,
        T_remaining=T_remaining,
        salary_preview=salary_preview,
        accuracy_rate=round(accuracy_rate, 2),
        H0=engineer.H0,
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
    now, today_start, month_start = _get_time_bounds()

    # 时间边界：昨日、上月
    yesterday_start = today_start - timedelta(days=1)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    # 上个月结束 = 本月1号
    last_month_end = month_start

    # 客资统计：今日/昨日/本月/上月（合并为一条 SQL）
    from sqlalchemy import case

    cr_status_cols = [
        func.sum(case((ClientResource.created_at >= today_start, 1), else_=0)).label("today_new_clients"),
        func.sum(case(
            (ClientResource.created_at >= yesterday_start, 1),
            (ClientResource.created_at < today_start, 1),
            else_=0
        )).label("yesterday_new_clients"),
        func.sum(case((ClientResource.created_at >= month_start, 1), else_=0)).label("monthly_new_clients"),
        func.sum(case(
            (ClientResource.created_at >= last_month_start, 1),
            (ClientResource.created_at < last_month_end, 1),
            else_=0
        )).label("last_month_new_clients"),
    ]
    cr_stmt = select(*cr_status_cols).where(ClientResource.pm_id == pm.id)
    result = await session.execute(cr_stmt)
    cr_row = result.one()
    today_new_clients = cr_row.today_new_clients or 0
    yesterday_new_clients = cr_row.yesterday_new_clients or 0
    monthly_new_clients = cr_row.monthly_new_clients or 0
    last_month_new_clients = cr_row.last_month_new_clients or 0

    # 我发布的任务总数 + 分状态计数
    from sqlalchemy import case

    task_status_cols = [
        func.count(case((Task.status == TaskStatus.UNCONFIRMED, 1), else_=None)).label("unconfirmed"),
        func.count(case((Task.status == TaskStatus.BIDDING, 1), else_=None)).label("bidding"),
        func.count(case((Task.status == TaskStatus.IN_PROGRESS, 1), else_=None)).label("in_progress"),
        func.count(case((Task.status == TaskStatus.PAUSED, 1), else_=None)).label("paused"),
        func.count(case((Task.status == TaskStatus.COMPLETED, 1), else_=None)).label("completed"),
        func.count(Task.id).label("total"),
    ]

    task_stmt = select(*task_status_cols).where(Task.pm_id == pm.id)
    result = await session.execute(task_stmt)
    row = result.one()

    return PMDashboard(
        user_id=pm.id,
        full_name=pm.full_name,
        today_new_clients=today_new_clients,
        yesterday_new_clients=yesterday_new_clients,
        monthly_new_clients=monthly_new_clients,
        last_month_new_clients=last_month_new_clients,
        pm_task_count=row.total or 0,
        task_count_unconfirmed=row.unconfirmed or 0,
        task_count_bidding=row.bidding or 0,
        task_count_in_progress=row.in_progress or 0,
        task_count_paused=row.paused or 0,
        task_count_completed=row.completed or 0,
        salary_preview=salary_preview,
        salary_detail_url="",
    )


async def get_admin_dashboard(
    *,
    session: AsyncSession,
    total_salary: float = 0.0,
    engineer_salary_cost: float = 0.0,
    pm_salary_cost: float = 0.0,
) -> AdminDashboard:
    """
    获取管理员仪表板数据

    Args:
        session: 数据库会话
        total_salary: 月度总收入（由调用方通过 calculate_user_salary 计算）
        engineer_salary_cost: 工程师总成本
        pm_salary_cost: PM 总成本

    Returns:
        AdminDashboard DTO
    """
    _, today_start, month_start = _get_time_bounds()

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
    ongoing_tasks = await get_ongoing_task_count(session=session)

    # 工程师负载：进行中任务数 + 本月实际工时 + 剩余工时 + T报准确率
    rows = await get_engineer_loads(session=session, month_start=month_start)
    engineer_loads = []
    for row in rows:
        T_monthly_plan = float(row.T_monthly_plan or 0)
        T_actual_monthly = float(row.T_actual_monthly or 0)
        T_remaining = max(0, T_monthly_plan - T_actual_monthly)

        T_actual_acc = float(row.T_actual_for_accuracy or 0)
        T_reported_acc = float(row.T_reported_for_accuracy or 0)
        accuracy_rate = min(T_actual_acc / T_reported_acc * 100, 100.0) if T_reported_acc > 0 else 100.0

        engineer_loads.append(EngineerLoad(
            user_id=row.id,
            full_name=row.full_name,
            current_tasks=row.ongoing_tasks or 0,
            T_actual_monthly=T_actual_monthly,
            T_remaining=round(T_remaining, 2),
            accuracy_rate=round(accuracy_rate, 2),
        ))

    # 星点排行榜 Top 10
    leaderboard = await get_leaderboard(session=session, limit=10)
    starpoint_ranks = [
        StarpointRank(
            user_id=row["engineer_id"],
            full_name=row["engineer_name"],
            current_starpoint=row["total_starpoints"] or 0,
        )
        for row in leaderboard
    ]

    return AdminDashboard(
        today_new_clients=today_new_clients,
        monthly_new_clients=monthly_new_clients,
        today_submitted_reports=today_submitted_reports,
        ongoing_tasks=ongoing_tasks,
        engineer_loads=engineer_loads,
        starpoint_ranks=starpoint_ranks,
        total_salary=total_salary,
        engineer_salary_cost=engineer_salary_cost,
        pm_salary_cost=pm_salary_cost,
    )
