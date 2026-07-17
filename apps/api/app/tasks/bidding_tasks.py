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

    业务逻辑：
    1. 检查任务是否存在且状态为 BIDDING
    2. 检查是否已过截止时间
    3. 计算所有报价的平均值
    4. 选择报价最接近均价的工程师中标
    5. 更新任务状态为 PENDING_START
    6. 设置 engineer_id

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

    # 5. 处理边界情况：无人报价
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

    # 6. 计算平均报价
    total_amount = sum(bid.amount for bid in bids)
    avg_amount = total_amount / len(bids)

    # 7. 选择中标人（报价最接近平均值）
    winner = min(bids, key=lambda b: abs(b.amount - avg_amount))

    # 8. 更新任务状态
    task.status = TaskStatus.PENDING_START
    task.engineer_id = winner.engineer_id
    await session.commit()

    logger.info(
        "winner_selected",
        task_id=task_id,
        winner_id=str(winner.engineer_id),
        winner_amount=winner.amount,
        avg_amount=avg_amount,
        bid_count=len(bids)
    )

    return {
        "task_id": task_id,
        "winner_id": str(winner.engineer_id),
        "winner_amount": winner.amount,
        "avg_amount": avg_amount,
        "bid_count": len(bids),
        "status": "success"
    }


# ==================== Celery 任务定义 ====================

@celery_app.task(bind=True, max_retries=3)
def settle_bidding_task(self, task_id: str) -> dict:
    """
    Celery 任务：竞价结算
    触发结算任务的 Celery 入口点。实际逻辑在 settle_bidding_task_async 中。

    参数:
        task_id: 任务ID (UUID字符串)

    返回:
        dict: 结算结果
    """
    logger.info(
        "settle_bidding_task_dispatched",
        task_id=task_id,
        celery_task_id=self.request.id,
    )
    # Celery 任务本身不执行异步操作，由 Beat 调度或 API 调用触发
    # 实际异步结算由 API 端点直接调用 settle_bidding_task_async
    return {
        "task_id": task_id,
        "status": "dispatched",
        "message": "Settlement task dispatched. Use API to execute."
    }