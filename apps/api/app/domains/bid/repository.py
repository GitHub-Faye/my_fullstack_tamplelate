"""
Bid 模块数据访问层（Repository）

负责竞价报价相关的数据库操作：CRUD、查询等。
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Bid, Task, TaskStatus


# ============================== Bid CRUD Operations ==============================

async def get_bid(*, session: AsyncSession, bid_id: uuid.UUID) -> Bid | None:
    """
    根据 ID 获取报价

    Args:
        session: 数据库会话
        bid_id: 报价 UUID

    Returns:
        Bid 对象或 None
    """
    return await session.get(Bid, bid_id)


async def get_bids_by_task(
    *,
    session: AsyncSession,
    task_id: uuid.UUID,
) -> List[Bid]:
    """
    获取任务的所有报价

    Args:
        session: 数据库会话
        task_id: 任务 ID

    Returns:
        报价列表
    """
    statement = select(Bid).where(Bid.task_id == task_id).order_by(Bid.created_at.desc())
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_bid_by_engineer_task(
    *,
    session: AsyncSession,
    task_id: uuid.UUID,
    engineer_id: uuid.UUID,
) -> Bid | None:
    """
    获取工程师对指定任务的报价

    Args:
        session: 数据库会话
        task_id: 任务 ID
        engineer_id: 工程师 ID

    Returns:
        Bid 对象或 None
    """
    statement = select(Bid).where(
        and_(Bid.task_id == task_id, Bid.engineer_id == engineer_id)
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_bids_by_engineer(
    *,
    session: AsyncSession,
    engineer_id: uuid.UUID,
) -> List[Bid]:
    """
    获取工程师的所有报价

    Args:
        session: 数据库会话
        engineer_id: 工程师 ID

    Returns:
        报价列表
    """
    statement = select(Bid).where(Bid.engineer_id == engineer_id).order_by(Bid.created_at.desc())
    result = await session.execute(statement)
    return list(result.scalars().all())


async def create_bid(
    *,
    session: AsyncSession,
    task_id: uuid.UUID,
    engineer_id: uuid.UUID,
    T_reported: float,
    H0: float = 100.0,  # 默认时薪 100
) -> Bid:
    """
    创建报价

    Args:
        session: 数据库会话
        task_id: 任务 ID
        engineer_id: 工程师 ID
        T_reported: 工程师报价工时
        H0: 时薪（默认 100）

    Returns:
        创建的报价对象
    """
    # 计算报价金额: amount = H0 × T_reported
    amount = H0 * T_reported

    db_bid = Bid(
        task_id=task_id,
        engineer_id=engineer_id,
        T_reported=T_reported,
        amount=amount,
    )
    session.add(db_bid)
    await session.commit()
    await session.refresh(db_bid)
    return db_bid


async def update_bid(
    *,
    session: AsyncSession,
    db_bid: Bid,
    T_reported: float,
    H0: float = 100.0,  # 默认时薪 100
) -> Bid:
    """
    更新报价

    Args:
        session: 数据库会话
        db_bid: 现有报价对象
        T_reported: 工程师报价工时
        H0: 时薪（默认 100）

    Returns:
        更新后的报价对象
    """
    # 重新计算报价金额
    amount = H0 * T_reported

    db_bid.T_reported = T_reported
    db_bid.amount = amount
    db_bid.updated_at = datetime.now(timezone.utc)

    session.add(db_bid)
    await session.commit()
    await session.refresh(db_bid)
    return db_bid


async def delete_bid(*, session: AsyncSession, db_bid: Bid) -> None:
    """
    删除报价

    Args:
        session: 数据库会话
        db_bid: 要删除的报价对象
    """
    await session.delete(db_bid)
    await session.commit()


async def count_bids_by_task(*, session: AsyncSession, task_id: uuid.UUID) -> int:
    """
    统计任务的报价数量

    Args:
        session: 数据库会话
        task_id: 任务 ID

    Returns:
        报价数量
    """
    statement = select(func.count()).select_from(Bid).where(Bid.task_id == task_id)
    result = await session.execute(statement)
    return result.scalar_one()
