# syntax=docker/dockerfile:1
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# 先复制 requirements.txt，利用 Docker 层缓存加速后续构建
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制整个项目代码
COPY . .

# 健康检查（无需 curl，使用 Python 内置方式）
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')"

# 默认 CMD（会被 docker-compose 中的 command 覆盖）
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]