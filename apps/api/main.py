from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router

from app.core.middleware import ProcessTimeMiddleware
from app.core.config import get_settings
from app.core.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行（Startup）
    print("Starting up...")   # 可选日志
    await init_db()           # 创建表（开发环境）或初始化连接池

    yield                     # ← 这里之后应用才开始接收请求

    # 关闭时执行（Shutdown）
    print("Shutting down...")
    # 如果有需要关闭的资源（如 engine.dispose()），写在这里

app = FastAPI(lifespan=lifespan)

app.add_middleware(ProcessTimeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
