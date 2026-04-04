# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件（利用 Docker 层缓存）
COPY requirements.txt .

# 安装 Python 依赖（使用 BuildKit 缓存挂载，已安装的包不会重复下载）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# 最后复制应用代码（代码变化时不影响上面的层）
COPY . .

# 设置 Python 路径
ENV PYTHONPATH=/app

# 默认命令（可被 docker-compose 覆盖）
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
