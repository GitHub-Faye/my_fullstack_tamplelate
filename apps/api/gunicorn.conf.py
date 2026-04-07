# gunicorn.conf.py
import multiprocessing

from app.core.config import get_settings

settings = get_settings()
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

# ================== 日志 ==================
accesslog = "-"                                   # 输出到 stdout（方便 Docker / systemd）
errorlog = "-"
loglevel = "info"                                 # 可改为 warning 或 debug

# 可选：自定义访问日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'