import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """
    请求处理时间中间件
    
    功能：
    - 记录请求处理时间
    - 添加 X-Process-Time 响应头
    - 记录结构化请求日志
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求 ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # 记录开始时间
        start_time = time.perf_counter()
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else None
        
        # 记录请求开始
        logger.info(
            "request_started",
            request_id=request_id,
            method=method,
            path=path,
            client_host=client_host,
            user_agent=request.headers.get("user-agent"),
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.perf_counter() - start_time
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            response.headers["X-Request-ID"] = request_id
            
            # 记录请求完成
            logger.info(
                "request_completed",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2),
            )
            
            return response
            
        except Exception as exc:
            # 计算处理时间（即使出错）
            process_time = time.perf_counter() - start_time
            
            # 记录请求错误
            logger.error(
                "request_failed",
                request_id=request_id,
                method=method,
                path=path,
                error_type=type(exc).__name__,
                error_message=str(exc),
                process_time_ms=round(process_time * 1000, 2),
                exc_info=True,
            )
            raise
