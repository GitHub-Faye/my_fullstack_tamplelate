"""
竞价模块 — 数据访问层

提供竞价报价和结算相关的 DB 操作。
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Bid, Task, TaskStatus, User, UserRoleType


# ========== 报价 CRUD ==========


async def get_bid(*, session: AsyncSession, bid_id: uuid.UUID) -> Bid | None:
    return await session.get(Bid, bid_id)


async def get_bids_by_task(
    *,
    session: AsyncSession,
    task_id: uuid.UUID,
) -> List[Bid]:
    stmt = select(Bid).where(Bid.task_id == task_id).order_by(Bid.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_bid_by_engineer_task(
    *,
    session: AsyncSession,
    task_id: uuid.UUID,
    engineer_id: uuid.UUID,
) -> Bid | None:
    stmt = select(Bid).where(and_(Bid.task_id == task_id, Bid.engineer_id == engineer_id))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_bids_by_engineer(
    *,
    session: AsyncSession,
    engineer_id: uuid.UUID,
) -> List[Bid]:
    stmt = select(Bid).where(Bid.engineer_id == engineer_id).order_by(Bid.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_bid(
    *,
    session: AsyncSession,
    task_id: uuid.UUID,
    engineer_id: uuid.UUID,
    T_reported: float,
    H0: float = 100.0,
) -> Bid:
    amount = H0 * T_reported
    db_bid = Bid(task_id=task_id, engineer_id=engineer_id, T_reported=T_reported, amount=amount)
    session.add(db_bid)
    await session.commit()
    await session.refresh(db_bid)
    return db_bid


async def update_bid(
    *,
    session: AsyncSession,
    db_bid: Bid,
    T_reported: float,
    H0: float = 100.0,
) -> Bid:
    amount = H0 * T_reported
    db_bid.T_reported = T_reported
    db_bid.amount = amount
    db_bid.updated_at = datetime.now(timezone.utc)
    session.add(db_bid)
    await session.commit()
    await session.refresh(db_bid)
    return db_bid


async def delete_bid(*, session: AsyncSession, db_bid: Bid) -> None:
    await session.delete(db_bid)
    await session.commit()


async def count_bids_by_task(*, session: AsyncSession, task_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(Bid).where(Bid.task_id == task_id)
    result = await session.execute(stmt)
    return result.scalar_one()


# ========== 结算逻辑 ==========


async def settle_bidding_task_async(session: AsyncSession, task_id: str, force: bool = False) -> dict:
    """
    异步执行竞价结算逻辑

    Spec §23: 计算所有报价的平均值，选择报价最接近均价的工程师中标。
    - 无人报价 → 回退到 UNCONFIRMED
    - 全部拒绝 → 回退到 UNCONFIRMED，进入下一轮

    force=True 时跳过截止时间检查（管理员手动结算使用）。
    """
    task_uuid = uuid.UUID(task_id)
    task_result = await session.execute(select(Task).where(Task.id == task_uuid))
    task = task_result.scalar_one_or_none()

    if not task:
        return {"task_id": task_id, "winner_id": None, "avg_amount": 0.0, "bid_count": 0, "status": "not_found"}

    if task.status != TaskStatus.BIDDING:
        return {"task_id": task_id, "winner_id": None, "avg_amount": 0.0, "bid_count": 0, "status": f"invalid_status:{task.status.value}"}

    if not force and task.bidding_deadline:
        deadline = task.bidding_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < deadline:
            return {"task_id": task_id, "winner_id": None, "avg_amount": 0.0, "bid_count": 0, "status": "deadline_not_reached"}

    # 查询所有报价
    bids_result = await session.execute(select(Bid).where(Bid.task_id == task_uuid))
    bids = bids_result.scalars().all()

    # 查询可竞价工程师人数
    engineer_result = await session.execute(select(User).where(User.role == UserRoleType.ENGINEER))
    all_engineers = engineer_result.scalars().all()
    total_engineers = len(all_engineers)

    # 无人报价
    if len(bids) == 0:
        task.status = TaskStatus.UNCONFIRMED
        task.bidding_deadline = None
        await session.commit()
        return {"task_id": task_id, "winner_id": None, "avg_amount": 0.0, "bid_count": 0, "status": "no_bids"}

    # 提前截止检查
    all_bid = len(bids) >= total_engineers

    # 计算平均报价，选择中标人
    total_amount = sum(bid.amount for bid in bids)
    avg_amount = total_amount / len(bids)
    winner = min(bids, key=lambda b: abs(b.amount - avg_amount))

    task.status = TaskStatus.PENDING_START
    task.engineer_id = winner.engineer_id
    await session.commit()

    return {
        "task_id": task_id,
        "winner_id": str(winner.engineer_id),
        "winner_amount": winner.amount,
        "avg_amount": avg_amount,
        "bid_count": len(bids),
        "early_close": all_bid,
        "status": "success",
    }