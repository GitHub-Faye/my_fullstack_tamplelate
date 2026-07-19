"""
竞价结算 Celery 任务（胶水层）

仅作为 Celery 调度胶水，核心逻辑在 domains/bidding/repository.py。
"""
from app.core.logging import get_logger
from app.tasks.celery_app import celery_app
from app.domains.bidding.repository import settle_bidding_task_async

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def settle_bidding_task(self, task_id: str) -> dict:
    """Celery 任务：竞价结算"""
    import asyncio
    from app.core.database import get_db

    logger.info("settle_bidding_task_started", task_id=task_id, celery_task_id=self.request.id)

    async def _run():
        async for session in get_db():
            return await settle_bidding_task_async(session, task_id)

    try:
        result = asyncio.run(_run())
        logger.info("settle_bidding_task_completed", task_id=task_id, status=result.get("status"))
        return result
    except Exception as e:
        logger.error("settle_bidding_task_failed", task_id=task_id, error=str(e))
        raise self.retry(exc=e)