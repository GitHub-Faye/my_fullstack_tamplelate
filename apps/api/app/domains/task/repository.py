"""
Task 模块数据访问层（Repository）

负责任务相关的数据库操作：CRUD、查询、统计等。
"""

import uuid
from datetime import date as date_type, datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Task, TaskStatus, TaskType, User, Bid
from app.domains.task.schemas import TaskCreate, TaskUpdate
from app.core.db_utils import paginated_query


# ============================== Task CRUD Operations ==============================

async def get_task(*, session: AsyncSession, task_id: uuid.UUID) -> Task | None:
    """
    根据 ID 获取任务

    Args:
        session: 数据库会话
        task_id: 任务 UUID

    Returns:
        Task 对象或 None
    """
    task = await session.get(Task, task_id)
    if task:
        await _fill_user_names(session, task)
    return task


async def get_tasks(
    *,
    session: AsyncSession,
    pm_id: Optional[uuid.UUID] = None,
    exclude_pm_id: bool = False,
    status: Optional[TaskStatus] = None,
    task_type: Optional[TaskType] = None,
    engineer_id: Optional[uuid.UUID] = None,
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[list[Task], int]:
    """
    获取任务列表（分页），支持按 PM、状态、类型、工程师和时间过滤

    Args:
        session: 数据库会话
        pm_id: PM ID 过滤（None 表示不过滤）
        exclude_pm_id: 是否排除 pm_id 指定的用户（用于「其他PM」筛选）
        status: 任务状态过滤（None 表示不过滤）
        task_type: 任务类型过滤（None 表示不过滤）
        engineer_id: 工程师 ID 过滤（None 表示不过滤）
        start_date: 创建时间起始日期（含）（None 表示不过滤）
        end_date: 创建时间结束日期（含）（None 表示不过滤）
        skip: 跳过记录数
        limit: 返回记录数上限

    Returns:
        (任务列表, 总数) 元组
    """
    # 构建条件列表
    conditions = []
    if pm_id and exclude_pm_id:
        conditions.append(Task.pm_id != pm_id)
    elif pm_id:
        conditions.append(Task.pm_id == pm_id)
    if status:
        conditions.append(Task.status == status)
    if task_type:
        conditions.append(Task.task_type == task_type)
    if engineer_id:
        conditions.append(Task.engineer_id == engineer_id)
    if start_date:
        conditions.append(Task.created_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc))
    if end_date:
        conditions.append(Task.created_at <= datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc))

    tasks, count = await paginated_query(
        session=session,
        model=Task,
        skip=skip,
        limit=limit,
        conditions=conditions if conditions else None,
        order_by=Task.created_at.desc(),
    )

    # 填充所有任务的姓名（批量查询）
    await _batch_fill_user_names(session, tasks)
    # 填充所有任务的竞价人数（批量查询）
    await _batch_fill_bid_counts(session, tasks)

    return tasks, count


async def _batch_fill_bid_counts(session: AsyncSession, tasks: list[Task]) -> None:
    """
    批量从 Bid 表填充每个任务的竞价人数（原地修改 task.bid_count）

    Args:
        session: 数据库会话
        tasks: 任务列表（原地修改）
    """
    if not tasks:
        return

    task_ids = [t.id for t in tasks if t.id]

    # 通过关联 Bid 表批量统计，避免 N+1
    stmt = (
        select(Bid.task_id, func.count(Bid.id))
        .where(Bid.task_id.in_(task_ids))
        .group_by(Bid.task_id)
    )
    result = await session.execute(stmt)
    bid_counts = {task_id: count for task_id, count in result.all()}

    for task in tasks:
        task.bid_count = bid_counts.get(task.id, 0)


async def _batch_fill_user_names(session: AsyncSession, tasks: list[Task]) -> None:
    """
    批量从关联 User 表填充 pm_name 和 engineer_name

    Args:
        session: 数据库会话
        tasks: 任务列表（原地修改）
    """
    if not tasks:
        return

    # 收集所有需要查询的用户 ID
    pm_ids = {t.pm_id for t in tasks if t.pm_id}
    engineer_ids = {t.engineer_id for t in tasks if t.engineer_id}
    all_ids = pm_ids | engineer_ids

    if not all_ids:
        return

    # 批量查询用户
    stmt = select(User).where(User.id.in_(all_ids))
    result = await session.execute(stmt)
    users = {u.id: u for u in result.scalars().all()}

    # 填充每个 task 的姓名
    for task in tasks:
        if task.pm_id:
            pm = users.get(task.pm_id)
            task.pm_name = pm.full_name if pm and pm.full_name else str(task.pm_id)[:8]
        if task.engineer_id:
            engineer = users.get(task.engineer_id)
            task.engineer_name = engineer.full_name if engineer and engineer.full_name else str(task.engineer_id)[:8]


async def _fill_user_names(session: AsyncSession, task: Task) -> None:
    """
    从关联 User 表填充 pm_name 和 engineer_name（单任务版本）

    Args:
        session: 数据库会话
        task: 任务对象（原地修改）
    """
    await _batch_fill_user_names(session, [task])


async def create_task(
    *,
    session: AsyncSession,
    task_in: TaskCreate,
    pm_id: uuid.UUID,
) -> Task:
    """
    创建新任务

    Args:
        session: 数据库会话
        task_in: 任务创建数据
        pm_id: PM 用户 ID

    Returns:
        创建的任务对象
    """
    db_task = Task.model_validate(
        task_in,
        update={
            "pm_id": pm_id,
            "status": TaskStatus.UNCONFIRMED,
        }
    )
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    await _fill_user_names(session, db_task)
    return db_task


async def update_task(
    *,
    session: AsyncSession,
    db_task: Task,
    task_in: TaskUpdate,
) -> Task:
    """
    更新任务

    Args:
        session: 数据库会话
        db_task: 现有任务对象
        task_in: 任务更新数据

    Returns:
        更新后的任务对象
    """
    update_data = task_in.model_dump(exclude_unset=True)
    db_task.sqlmodel_update(update_data)
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    await _fill_user_names(session, db_task)
    return db_task


async def delete_task(*, session: AsyncSession, db_task: Task) -> None:
    """
    删除任务

    Args:
        session: 数据库会话
        db_task: 要删除的任务对象
    """
    await session.delete(db_task)
    await session.commit()


async def count_tasks_by_pm(*, session: AsyncSession, pm_id: uuid.UUID) -> int:
    """
    统计 PM 创建的任务数量

    Args:
        session: 数据库会话
        pm_id: PM 用户 ID

    Returns:
        任务数量
    """
    statement = select(func.count()).select_from(Task).where(Task.pm_id == pm_id)
    result = await session.execute(statement)
    return result.scalar_one()


async def can_update_task(*, session: AsyncSession, task: Task) -> bool:
    """
    检查任务是否可被编辑

    只有 "未确认" 状态的任务可被 PM 编辑

    Args:
        session: 数据库会话
        task: 任务对象

    Returns:
        是否可编辑
    """
    return task.status == TaskStatus.UNCONFIRMED


async def get_ongoing_task_count(
    *,
    session: AsyncSession,
) -> int:
    """
    获取进行中的任务数。

    Args:
        session: 数据库会话

    Returns:
        进行中任务数量
    """
    stmt = select(func.count()).select_from(Task).where(
        Task.status == TaskStatus.IN_PROGRESS
    )
    result = await session.execute(stmt)
    return result.scalar_one() or 0