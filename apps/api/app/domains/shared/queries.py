"""
共享查询模块

集中放置跨域使用的 SQL 查询函数，消除各 repository 之间的重复查询。
"""
import uuid
from datetime import datetime, timezone
from typing import Tuple

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Task, TaskStatus, User, UserRoleType


async def get_engineer_monthly_hours(
    *,
    session: AsyncSession,
    engineer_id: uuid.UUID,
) -> Tuple[float, float]:
    """
    获取工程师本月完成任务的 T实 和 T报 合计。

    由 salary 和 dashboard 模块共享使用。

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
                Task.engineer_id == engineer_id,
                Task.status == TaskStatus.COMPLETED,
                Task.updated_at >= month_start,
            )
        )
    )
    result = await session.execute(stmt)
    row = result.one()
    return float(row.T_actual_total or 0), float(row.T_reported_total or 0)


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
            func.coalesce(func.sum(Task.T_actual).filter(
                and_(
                    Task.status == TaskStatus.COMPLETED,
                    Task.updated_at >= month_start,
                )
            ), 0).label("T_actual_monthly"),
            func.coalesce(func.sum(Task.T_actual).filter(
                and_(
                    Task.status == TaskStatus.COMPLETED,
                    Task.updated_at >= month_start,
                    Task.T_reported > 0,
                )
            ), 0).label("T_actual_for_accuracy"),
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