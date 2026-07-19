"""
Task 模块数据访问层（Repository）

负责任务相关的数据库操作：CRUD、查询、统计等。
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Task, TaskStatus
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
    return await session.get(Task, task_id)


async def get_tasks(
    *,
    session: AsyncSession,
    pm_id: Optional[uuid.UUID] = None,
    status: Optional[TaskStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[list[Task], int]:
    """
    获取任务列表（分页），支持按 PM 和状态过滤

    Args:
        session: 数据库会话
        pm_id: PM ID 过滤（None 表示不过滤）
        status: 任务状态过滤（None 表示不过滤）
        skip: 跳过记录数
        limit: 返回记录数上限

    Returns:
        (任务列表, 总数) 元组
    """
    # 构建条件列表
    conditions = []
    if pm_id:
        conditions.append(Task.pm_id == pm_id)
    if status:
        conditions.append(Task.status == status)

    return await paginated_query(
        session=session,
        model=Task,
        skip=skip,
        limit=limit,
        conditions=conditions if conditions else None,
        order_by=Task.created_at.desc(),
    )


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