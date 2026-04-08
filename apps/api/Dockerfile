# syntax=docker/dockerfile:1
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# 安装系统依赖（PostgreSQL、Celery 等常用依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制 requirements.txt，利用 Docker 层缓存加速后续构建
COPY requirements.txt .

# 安装 Python 依赖（推荐使用缓存挂载，构建更快）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制整个项目代码（开发时会被 docker-compose volume 覆盖）
COPY . .

# ==================== 可选：添加健康检查脚本（推荐） ====================
# 如果你想让 celery-worker 有更好的健康检查，可以后续再加

# 默认 CMD（会被 docker-compose 中的 command 覆盖，所以不用太在意）
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]