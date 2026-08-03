"""
竞价后台调度 — 自动结算与自动重新发布

启动时在 FastAPI lifespan 中拉起一个后台 asyncio 协程，周期性扫描
已过 bidding_deadline 的 BIDDING 任务并自动结算（全量扫描，天然幂等）：

- 有人报价 → 自动挑选最接近均价的工程师中标（PENDING_START）
- 无人报价 → 自动重新发布（生成新的 bidding_deadline，重新倒计时竞价）

Celery 已移除，改用轻量的 asyncio 后台任务。

时区约定：bidding_deadline 在 MySQL 中存储为本地（服务器 +08:00）时间，
读回后为 naive datetime。调度器统一使用 naive local 时间做比较，避免
aware/naive 不一致导致的误判。
"""
import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select, and_

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.core.models import Task, TaskStatus
from app.domains.bidding.repository import settle_bidding_task_async

logger = get_logger(__name__)


# 重新发布时的新竞价窗口（天）
DEFAULT_REPUBLISH_DAYS = 1


def _now_local() -> datetime:
    """返回服务器本地时间（naive），用于与 DB 中 naive deadline 对比。"""
    return datetime.now()


async def settle_overdue_bidding_tasks() -> None:
    """扫描所有已过截止时间但仍处于 BIDDING 状态的任务并结算"""
    now = _now_local()

    async with AsyncSessionLocal() as session:
        stmt = select(Task).where(and_(Task.status == TaskStatus.BIDDING))
        result = await session.execute(stmt)
        tasks = result.scalars().all()

        for task in tasks:
            deadline = task.bidding_deadline
            if not deadline:
                continue
            # deadline 在 DB 中为 naive local 时间，直接与 now 比较
            if now < deadline:
                continue  # 截止时间未到，跳过

            outcome = await settle_bidding_task_async(session, str(task.id))

            if outcome["status"] == "success":
                logger.info(
                    "bidding_auto_settled",
                    task_id=str(task.id),
                    winner_id=outcome["winner_id"],
                    bid_count=outcome["bid_count"],
                )
            elif outcome["status"] == "no_bids":
                await _republish(session, task)
            else:
                logger.warning(
                    "bidding_auto_settle_skipped",
                    task_id=str(task.id),
                    status=outcome["status"],
                )


async def _republish(session, task: Task) -> None:
    """无人竞价：重新发布，重置竞价截止时间"""
    task.bidding_deadline = datetime.now() + timedelta(days=DEFAULT_REPUBLISH_DAYS)
    task.status = TaskStatus.BIDDING
    session.add(task)
    await session.commit()
    logger.info(
        "bidding_no_bids_republished",
        task_id=str(task.id),
        new_deadline=str(task.bidding_deadline),
    )


async def bidding_scheduler_loop(interval_seconds: int = 30) -> None:
    """后台调度协程，每隔 interval_seconds 扫描一次"""
    logger.info("bidding_scheduler_started", interval_seconds=interval_seconds)
    try:
        while True:
            try:
                await settle_overdue_bidding_tasks()
            except Exception as exc:  # noqa: BLE001 — 调度循环需在异常后继续
                logger.error("bidding_scheduler_scan_failed", error=str(exc))
            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        logger.info("bidding_scheduler_stopped")
        raise
