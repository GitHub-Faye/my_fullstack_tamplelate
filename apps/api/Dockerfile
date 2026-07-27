# syntax=docker/dockerfile:1
FROM python:3.11-slim

# 安装 uv 包管理器（比 pip 快 10-100 倍）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
    UV_INDEX_URL=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

WORKDIR /app

# 先复制依赖锁定文件，利用 Docker 层缓存
COPY pyproject.toml uv.lock ./

# 安装生产依赖（不安装 dev 依赖，减小镜像体积）
RUN uv sync --no-dev --locked --no-install-project

# 复制整个项目代码
COPY . .

# 安装项目自身
RUN uv sync --no-dev --locked

# 健康检查（使用 Python 内置方式，无需 curl）
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')"

# 默认 CMD（会被 docker-compose 中的 command 覆盖）
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]