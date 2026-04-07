"""
结构化日志配置模块 - 使用 structlog

提供统一的结构化日志配置，支持：
- JSON 格式输出（生产环境）
- 彩色控制台输出（开发环境）
- 与标准库 logging 的桥接
- FastAPI 和 Celery 集成
"""

import logging
import logging.config
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from app.core.config import get_settings


settings = get_settings()


def add_app_info(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    添加应用信息到日志事件
    
    包括：
    - app_name: 应用名称
    - environment: 运行环境
    - service: 服务标识
    """
    event_dict["app_name"] = settings.PROJECT_NAME
    event_dict["environment"] = settings.ENVIRONMENT
    event_dict["service"] = "api"
    return event_dict


def configure_logging() -> None:
    """
    配置结构化日志系统
    
    包括：
    1. 标准库 logging 配置
    2. structlog 配置
    3. 处理器和格式化器设置
    """
    # 判断是否为开发环境
    is_development = settings.ENVIRONMENT == "local"
    
    # 共享的处理器列表
    handlers = ["console"]
    
    # 标准库 logging 配置 - 使用简单格式，让 structlog 处理详细格式
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "format": "%(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "plain",
            },
        },
        "loggers": {
            "": {
                "handlers": handlers,
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "propagate": True,
            },
            "uvicorn": {
                "handlers": handlers,
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": handlers,
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": handlers,
                "level": "WARNING",
                "propagate": False,
            },
            "celery": {
                "handlers": handlers,
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    
    # 应用标准库 logging 配置
    logging.config.dictConfig(logging_config)
    
    # structlog 配置
    shared_processors = [
        # 添加时间戳
        structlog.processors.TimeStamper(fmt="iso"),
        # 添加日志级别
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        # 添加应用信息
        add_app_info,
        # 格式化异常信息
        structlog.processors.format_exc_info,
    ]
    
    if is_development:
        # 开发环境：彩色控制台输出
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # 生产环境：JSON 输出
        processors = shared_processors + [
            structlog.processors.JSONRenderer(),
        ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    获取结构化日志记录器
    
    Args:
        name: 日志记录器名称，通常为模块名
        
    Returns:
        structlog.stdlib.BoundLogger: 绑定的结构化日志记录器
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("user_logged_in", user_id=123, ip="192.168.1.1")
    """
    return structlog.get_logger(name)


# 预配置的日志记录器实例（用于应用启动前）
logger = get_logger("app.core.logging")
