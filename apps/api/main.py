from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import router as api_router

from app.core.errors import BusinessException
from app.core.middleware import ProcessTimeMiddleware
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import configure_logging, get_logger

import sentry_sdk

# 首先配置日志系统（在应用启动前）
configure_logging()

settings = get_settings()
logger = get_logger(__name__)

# ================== Sentry 集成（可选） ==================
# sentry_sdk.init(
#     dsn="https://b3de48eedad92f89c06ef7f45c6bd58f@o4511178754686976.ingest.us.sentry.io/4511178758029312",
#     # Add data like request headers and IP for users,
#     # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
#     send_default_pii=True,
# )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行（Startup）
    logger.info(
        "application_starting",
        app_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
    )
    await init_db()  # 创建表（开发环境）或初始化连接池
    logger.info("database_initialized")

    yield  # ← 这里之后应用才开始接收请求

    # 关闭时执行（Shutdown）
    logger.info("application_shutting_down")


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    version="1.0.0",
)


@app.exception_handler(BusinessException)
async def business_exception_handler(
    request: Request, exc: BusinessException
) -> JSONResponse:
    """将业务异常统一序列化为标准错误响应。"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """将请求校验异常统一序列化为标准错误响应。"""
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "code": "SYSTEM_VALIDATION_ERROR",
        },
    )


app.add_middleware(ProcessTimeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# @app.get("/sentry-debug")
# async def trigger_error():
#     division_by_zero = 1 / 0

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
