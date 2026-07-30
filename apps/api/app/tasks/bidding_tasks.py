"""
竞价结算 — 同步版本（Celery 已移除）

核心逻辑在 domains/bidding/repository.py。
"""
from app.core.logging import get_logger
from app.domains.bidding.repository import settle_bidding_task_async

logger = get_logger(__name__)


async def settle_bidding_task_sync(task_id: str) -> dict:
    """同步执行竞价结算"""
    from app.core.database import get_db

    logger.info("settle_bidding_task_started", task_id=task_id)

    async for session in get_db():
        result = await settle_bidding_task_async(session, task_id)
        logger.info("settle_bidding_task_completed", task_id=task_id, status=result.get("status"))
        return result