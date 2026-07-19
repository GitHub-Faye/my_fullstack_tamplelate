"""
竞价结算任务模块

提供竞价截止后的自动结算功能：
- 计算中标人
- 更新任务状态
- 触发结算任务
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.models import Task, TaskStatus, Bid, User, UserRoleType
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


async def settle_bidding_task_async(session: AsyncSession, task_id: str) -> dict:
    """
    异步执行竞价结算逻辑

    业务逻辑（Spec §23）：
    1. 检查任务是否存在且状态为 BIDDING
    2. 检查是否已过截止时间（或已提前截止）
    3. 计算所有报价的平均值
    4. 选择报价最接近均价的工程师中标
    5. 更新任务状态为 PENDING_START
    6. 设置 engineer_id

    边界情况：
    - 无人报价 → 回退到 CONFIRMED_UNPUBLISHED
    - 全部拒绝 → 回退到 CONFIRMED_UNPUBLISHED，进入下一轮

    参数:
        session: 数据库会话
        task_id: 任务ID (UUID字符串)

    返回:
        dict: 结算结果
    """
    # 1. 查询任务
    task_uuid = uuid.UUID(task_id)
    task_result = await session.execute(
        select(Task).where(Task.id == task_uuid)
    )
    task = task_result.scalar_one_or_none()

    if not task:
        logger.warning("task_not_found", task_id=task_id)
        return {
            "task_id": task_id,
            "winner_id": None,
            "avg_amount": 0.0,
            "bid_count": 0,
            "status": "not_found"
        }

    # 2. 检查任务状态
    if task.status != TaskStatus.BIDDING:
        logger.warning(
            "task_not_in_bidding_status",
            task_id=task_id,
            current_status=task.status.value
        )
        return {
            "task_id": task_id,
            "winner_id": None,
            "avg_amount": 0.0,
            "bid_count": 0,
            "status": f"invalid_status:{task.status.value}"
        }

    # 3. 检查截止时间
    if task.bidding_deadline:
        deadline = task.bidding_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) < deadline:
            logger.warning(
                "bidding_deadline_not_reached",
                task_id=task_id,
                deadline=str(deadline)
            )
            return {
                "task_id": task_id,
                "winner_id": None,
                "avg_amount": 0.0,
                "bid_count": 0,
                "status": "deadline_not_reached"
            }

    # 4. 查询所有报价
    bids_result = await session.execute(
        select(Bid).where(Bid.task_id == task_uuid)
    )
    bids = bids_result.scalars().all()

    # 5. 查询所有工程师（用于计算总应报价人数）
    # 查询所有工程师角色用户
    engineer_result = await session.execute(
        select(User).where(User.role == UserRoleType.ENGINEER)
    )
    all_engineers = engineer_result.scalars().all()
    total_engineers = len(all_engineers)

    # 6. 查询所有报价
    bids_result = await session.execute(
        select(Bid).where(Bid.task_id == task_uuid)
    )
    bids = bids_result.scalars().all()

    # 7. 处理边界情况：无人报价
    if len(bids) == 0:
        task.status = TaskStatus.CONFIRMED_UNPUBLISHED
        task.bidding_deadline = None
        await session.commit()

        logger.info(
            "no_bids_received",
            task_id=task_id,
            action="reverted_to_confirmed_unpublished"
        )

        return {
            "task_id": task_id,
            "winner_id": None,
            "avg_amount": 0.0,
            "bid_count": 0,
            "status": "no_bids"
        }

    # 8. 检查是否所有工程师都已报价（提前截止条件）
    all_bid = len(bids) >= total_engineers
    if all_bid:
        logger.info(
            "all_engineers_bid_early_close",
            task_id=task_id,
            bid_count=len(bids),
            total_engineers=total_engineers,
        )

    # 9. 计算平均报价
    total_amount = sum(bid.amount for bid in bids)
    avg_amount = total_amount / len(bids)

    # 10. 选择中标人（报价最接近平均值）
    winner = min(bids, key=lambda b: abs(b.amount - avg_amount))

    # 11. 检查中标人是否拒绝（全部拒绝 → 进入下一轮）
    # 简单实现：如果中标人拒绝，回退到 CONFIRMED_UNPUBLISHED
    # 注意：工程师通过 /tasks/{id}/decline 拒绝后，状态已变更，
    # 此处不额外处理"全部拒绝"逻辑，该逻辑由 decline 端点实现

    # 12. 更新任务状态
    task.status = TaskStatus.PENDING_START
    task.engineer_id = winner.engineer_id
    await session.commit()

    logger.info(
        "winner_selected",
        task_id=task_id,
        winner_id=str(winner.engineer_id),
        winner_amount=winner.amount,
        avg_amount=avg_amount,
        bid_count=len(bids),
        early_close=all_bid,
    )

    return {
        "task_id": task_id,
        "winner_id": str(winner.engineer_id),
        "winner_amount": winner.amount,
        "avg_amount": avg_amount,
        "bid_count": len(bids),
        "early_close": all_bid,
        "status": "success"
    }


# ==================== Celery 任务定义 ====================

@celery_app.task(bind=True, max_retries=3)
def settle_bidding_task(self, task_id: str) -> dict:
    """
    Celery 任务：竞价结算

    执行完整的竞价结算逻辑：
    1. 计算所有报价的平均值
    2. 选择报价最接近均价的工程师中标
    3. 更新任务状态为 PENDING_START
    4. 设置 engineer_id

    参数:
        task_id: 任务ID (UUID字符串)

    返回:
        dict: 结算结果
    """
    import asyncio
    from app.core.database import get_db

    logger.info(
        "settle_bidding_task_started",
        task_id=task_id,
        celery_task_id=self.request.id,
    )

    async def _run():
        async for session in get_db():
            result = await settle_bidding_task_async(session, task_id)
            return result

    try:
        result = asyncio.run(_run())
        logger.info(
            "settle_bidding_task_completed",
            task_id=task_id,
            status=result.get("status"),
        )
        return result
    except Exception as e:
        logger.error(
            "settle_bidding_task_failed",
            task_id=task_id,
            error=str(e),
        )
        raise self.retry(exc=e)