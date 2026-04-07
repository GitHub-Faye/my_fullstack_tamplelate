from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, worker_ready, worker_shutdown

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

# 首先配置日志
configure_logging()

settings = get_settings()
logger = get_logger(__name__)

# 创建 Celery 应用 —— 明确分开 Broker 和 Backend（推荐做法）
celery_app = Celery(
    "app",
    # Broker 使用 RabbitMQ（生产首选）
    broker=settings.CELERY_BROKER_URL,           # ← 重点修改这里
    # Backend 继续使用 Redis（速度快，适合存结果）
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
    
    include=[
        "app.tasks.email_tasks",
        "app.tasks.user_tasks",
    ],
)

# Celery 生产配置（强烈建议增加这些）
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,          # 30 分钟超时
    worker_prefetch_multiplier=1,     # 生产强烈推荐设为 1
    
    # RabbitMQ 相关重要配置
    broker_connection_retry_on_startup=True,   # RabbitMQ 未就绪时自动重试
    broker_pool_limit=10,                      # 连接池大小
    task_acks_late=True,                       # 任务执行完再确认，防止任务丢失
    task_reject_on_worker_lost=True,
    
    # 结果过期，防止 Redis 无限增长
    result_expires=3600 * 24,                  # 24 小时过期
    worker_max_tasks_per_child=1000,           # 防止内存泄漏
)


# ==================== Celery 信号处理器（结构化日志） ====================

@worker_ready.connect
def on_worker_ready(**kwargs):
    """Worker 就绪时记录日志"""
    logger.info(
        "celery_worker_ready",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
    )


@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    """Worker 关闭时记录日志"""
    logger.info("celery_worker_shutdown")


@task_prerun.connect
def on_task_prerun(task_id, task, args, kwargs, **extras):
    """任务开始执行时记录日志"""
    logger.info(
        "celery_task_started",
        task_id=task_id,
        task_name=task.name,
        task_args=str(args) if args else None,
        task_kwargs=str(kwargs) if kwargs else None,
    )


@task_postrun.connect
def on_task_postrun(task_id, task, retval, state, **extras):
    """任务完成时记录日志"""
    logger.info(
        "celery_task_completed",
        task_id=task_id,
        task_name=task.name,
        task_state=state,
    )


@task_failure.connect
def on_task_failure(task_id, task, exception, args, kwargs, traceback, einfo, **extras):
    """任务失败时记录日志"""
    logger.error(
        "celery_task_failed",
        task_id=task_id,
        task_name=task.name,
        error_type=type(exception).__name__,
        error_message=str(exception),
        task_args=str(args) if args else None,
        exc_info=True,
    )


if __name__ == "__main__":
    celery_app.start()
