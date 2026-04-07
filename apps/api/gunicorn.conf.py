# gunicorn.conf.py
import multiprocessing

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

# 首先配置日志
configure_logging()

settings = get_settings()
logger = get_logger(__name__)

# ================== 基本配置 ==================
bind = settings.BIND or "0.0.0.0:8000"          # 监听地址，可通过环境变量修改
backlog = 2048                                    # 等待队列长度

# ================== Worker 配置 ==================
# 对于纯异步 FastAPI，推荐 worker 数 ≈ CPU核心数（而不是 2*cores+1）
workers = int(settings.WORKERS or 4)            # worker 数量，默认 4（可通过环境变量修改）
worker_class = "uvicorn.workers.UvicornWorker"    # 关键：使用 Uvicorn 的 ASGI worker
preload_app = True                                # 预加载，节省内存（推荐）

# ================== 超时与连接 ==================
timeout = 120                                     # worker 超时时间（秒）
graceful_timeout = 30                             # 优雅关闭时间
keepalive = 5                                     # keep-alive 时间
worker_connections = 1000                         # 每个 worker 最大并发连接

# ================== 防内存泄漏 ==================
max_requests = 1000                               # 处理多少请求后重启 worker
max_requests_jitter = 100                         # 随机抖动，避免同时重启

# ================== 日志配置（使用 structlog） ==================
# 禁用 gunicorn 默认日志，使用 structlog
accesslog = None                                  # 禁用默认访问日志
errorlog = "-"                                    # 错误输出到 stdout
loglevel = "info"                                 # 日志级别

# 使用自定义日志配置
capture_output = True                             # 捕获 stdout/stderr
enable_stdio_inheritance = True                   # 继承 stdio


def on_starting(server):
    """服务器启动时调用"""
    logger.info(
        "gunicorn_starting",
        workers=workers,
        bind=bind,
        environment=settings.ENVIRONMENT,
    )


def on_reload(server):
    """重新加载配置时调用"""
    logger.info("gunicorn_reloading")


def when_ready(server):
    """服务器就绪时调用"""
    logger.info(
        "gunicorn_ready",
        workers=workers,
        bind=bind,
    )


def worker_int(worker):
    """worker 收到 SIGINT 或 SIGQUIT 时调用"""
    logger.warning(
        "gunicorn_worker_interrupted",
        worker_pid=worker.pid,
    )


def worker_abort(worker):
    """worker 收到 SIGABRT 时调用"""
    logger.error(
        "gunicorn_worker_aborted",
        worker_pid=worker.pid,
    )


def on_exit(server):
    """服务器退出时调用"""
    logger.info("gunicorn_exiting")
