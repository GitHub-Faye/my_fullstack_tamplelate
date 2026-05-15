# Tasks 目录 - 异步任务队列

## 目录作用

`tasks` 目录是后端 API 的**异步任务队列**模块，用于处理耗时操作、定时任务和后台任务。通过将同步阻塞操作转为异步执行，提高 API 响应速度和系统吞吐量。

### 核心职责

1. **异步任务执行** - 将耗时操作（如发送邮件、数据处理、文件生成）放入后台执行
2. **任务调度** - 支持定时任务、周期性任务的调度执行
3. **任务重试机制** - 失败任务自动重试，提高任务成功率
4. **分布式任务处理** - 支持多 Worker 分布式消费任务队列

## 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| 任务队列框架 | [Celery](https://docs.celeryq.dev/) | Python 分布式任务队列 |
| 消息代理 | RabbitMQ | 任务消息队列（Broker） |
| 结果存储 | Redis | 任务结果缓存与状态存储 |
| 序列化 | JSON | 任务参数与结果序列化 |

## 目录结构

```
tasks/
├── __init__.py          # 模块导出，暴露 celery_app 实例
├── celery_app.py        # Celery 应用配置与初始化
├── tasks.md            # 本文档
├── email_tasks.py      # 邮件相关任务
└── user_tasks.py       # 用户相关任务
```

## 增量开发指南

### 1. 创建新任务文件

当需要添加新的业务领域任务时，创建新的任务文件：

```python
# app/tasks/report_tasks.py
from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def generate_report_task(self, report_id: str, user_id: str) -> str:
    """
    异步生成报表任务
    
    参数:
        report_id: 报表ID
        user_id: 用户ID
    
    返回:
        str: 生成的文件路径
    """
    try:
        logger.info(
            "generating_report",
            report_id=report_id,
            user_id=user_id,
            task_id=self.request.id,
        )
        
        # TODO: 实现报表生成逻辑
        
        logger.info("report_generated", report_id=report_id)
        return "/path/to/report.pdf"
        
    except Exception as exc:
        logger.error(
            "report_generation_failed",
            report_id=report_id,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=60)
```

### 2. 注册任务模块

在 [`celery_app.py`](celery_app.py:21) 的 `include` 列表中添加新模块：

```python
celery_app = Celery(
    "app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.user_tasks",
        "app.tasks.report_tasks",  # ← 新增
    ],
)
```

### 3. 调用任务

在业务代码中异步触发任务：

```python
from app.tasks.report_tasks import generate_report_task

# 异步执行（立即返回，不等待结果）
generate_report_task.delay(report_id="123", user_id="user-456")

# 或者使用 apply_async 进行高级配置
generate_report_task.apply_async(
    args=["123", "user-456"],
    countdown=60,  # 延迟60秒执行
    queue="reports",  # 指定队列
)
```

## 任务配置规范

### 装饰器参数

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `bind=True` | 绑定任务实例，可访问 `self` | 必须 |
| `max_retries` | 最大重试次数 | 3-5 次 |
| `default_retry_delay` | 默认重试间隔（秒） | 60-300 |
| `time_limit` | 任务执行时间限制（秒） | 根据业务设定 |

### 任务编写规范

1. **必须添加类型注解** - 参数和返回值都要有类型提示
2. **必须包含文档字符串** - 说明任务功能、参数、返回值
3. **必须记录日志** - 使用结构化日志记录任务生命周期
4. **必须实现重试** - 捕获异常并使用 `self.retry()` 重试
5. **避免在任务中传递大对象** - 使用 ID 而非对象实例

## 运行 Worker

```bash
# 开发环境
celery -A app.tasks worker --loglevel=info

# 生产环境（多进程）
celery -A app.tasks worker --loglevel=info --concurrency=4

# 指定队列
celery -A app.tasks worker --loglevel=info -Q emails,users
```

## 监控任务

- 任务状态存储在 Redis 中，可通过 `AsyncResult` 查询
- 日志中包含 `task_id` 字段，便于追踪任务执行链路
- 生产环境建议配合 Flower 等监控工具
