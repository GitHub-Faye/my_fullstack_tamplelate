"""
共享查询模块

集中放置跨域使用的 SQL 查询函数，消除各 repository 之间的重复查询。
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Task, TaskStatus, User, UserRoleType


async def get_engineer_monthly_hours(
    *,
    session: AsyncSession,
    engineer_id: uuid.UUID,
    month: Optional[str] = None,
) -> Tuple[float, float]:
    """
    获取工程师某月完成任务的 T有效、T报价 合计。

    T_effective 用于工资计算，T_reported 用于统计参考。

    Args:
        month: 月份 YYYY-MM，默认当前月

    Returns:
        (T_effective_total, T_reported_total) 元组
    """
    if month:
        month_start = datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc)
    else:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if month:
        # 计算下个月第一天作为结束
        year, mon = map(int, month.split("-"))
        if mon == 12:
            month_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            month_end = datetime(year, mon + 1, 1, tzinfo=timezone.utc)
        conditions = [
            Task.engineer_id == engineer_id,
            Task.status == TaskStatus.COMPLETED,
            Task.updated_at >= month_start,
            Task.updated_at < month_end,
        ]
    else:
        conditions = [
            Task.engineer_id == engineer_id,
            Task.status == TaskStatus.COMPLETED,
            Task.updated_at >= month_start,
        ]

    stmt = (
        select(
            func.coalesce(func.sum(Task.T_effective), 0).label("T_effective_total"),
            func.coalesce(func.sum(Task.T_reported), 0).label("T_reported_total"),
        )
        .where(and_(*conditions))
    )
    result = await session.execute(stmt)
    row = result.one()
    return float(row.T_effective_total or 0), float(row.T_reported_total or 0)


async def get_engineer_loads(
    *,
    session: AsyncSession,
    month_start: datetime,
) -> list[dict]:
    """
    获取所有工程师的负载数据（进行中任务数、本月工时、准确率）。

    由 user 和 dashboard 模块共享使用。
    """
    stmt = (
        select(
            User.id,
            User.full_name,
            User.T_monthly_plan,
            func.count(Task.id).filter(Task.status == TaskStatus.IN_PROGRESS).label("ongoing_tasks"),
            func.coalesce(func.sum(Task.T_effective).filter(
                and_(
                    Task.status == TaskStatus.COMPLETED,
                    Task.updated_at >= month_start,
                )
            ), 0).label("T_effective_monthly"),
            func.coalesce(func.sum(Task.T_effective).filter(
                and_(
                    Task.status == TaskStatus.COMPLETED,
                    Task.updated_at >= month_start,
                    Task.T_reported > 0,
                )
            ), 0).label("T_effective_for_accuracy"),
            func.coalesce(func.sum(Task.T_reported).filter(
                and_(
                    Task.status == TaskStatus.COMPLETED,
                    Task.updated_at >= month_start,
                    Task.T_reported > 0,
                )
            ), 0).label("T_reported_for_accuracy"),
        )
        .select_from(User)
        .outerjoin(Task, Task.engineer_id == User.id)
        .where(User.role == UserRoleType.ENGINEER)
        .group_by(User.id, User.full_name, User.T_monthly_plan)
    )
    result = await session.execute(stmt)
    return result.all()