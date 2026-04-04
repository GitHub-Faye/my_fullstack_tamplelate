from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# 创建 Celery 应用
celery_app = Celery(
    "app",
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.user_tasks",
    ],
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
)

if __name__ == "__main__":
    celery_app.start()
