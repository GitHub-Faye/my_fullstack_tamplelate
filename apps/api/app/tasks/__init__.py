from app.core.logging import get_logger

logger = get_logger(__name__)

# Celery 已移除。所有任务改为同步执行。

# 如需异步任务，后续可引入 arq 或更轻量的方案。