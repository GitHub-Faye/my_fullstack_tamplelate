"""
统一错误体系模块

定义系统中所有的错误码和统一异常类，确保前后端错误语义一致。
错误码格式: DOMAIN_ACTION_DETAIL
"""

from enum import Enum
from typing import Any

from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    """
    业务错误码枚举
    
    格式规范: DOMAIN_ACTION_DETAIL
    - DOMAIN: 领域/模块 (AUTH, USER, ITEM, SYSTEM)
    - ACTION: 操作 (INVALID, NOT_FOUND, ALREADY_EXISTS, FORBIDDEN, etc.)
    - DETAIL: 具体细节 (可选)
    """
    
    # ==================== 认证相关错误 (AUTH) ====================
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_EXPIRED_TOKEN = "AUTH_EXPIRED_TOKEN"
    AUTH_INACTIVE_USER = "AUTH_INACTIVE_USER"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"
    AUTH_MISSING_SCOPE = "AUTH_MISSING_SCOPE"
    
    # ==================== 用户相关错误 (USER) ====================
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_EMAIL_ALREADY_EXISTS = "USER_EMAIL_ALREADY_EXISTS"
    USER_INVALID_PASSWORD = "USER_INVALID_PASSWORD"
    USER_PASSWORD_SAME_AS_OLD = "USER_PASSWORD_SAME_AS_OLD"
    USER_CANNOT_DELETE_SELF = "USER_CANNOT_DELETE_SELF"
    USER_CANNOT_DELETE_SUPERUSER = "USER_CANNOT_DELETE_SUPERUSER"
    
    # ==================== 物品相关错误 (ITEM) ====================
    ITEM_NOT_FOUND = "ITEM_NOT_FOUND"
    ITEM_NOT_OWNER = "ITEM_NOT_OWNER"
    
    # ==================== 系统错误 (SYSTEM) ====================
    SYSTEM_INTERNAL_ERROR = "SYSTEM_INTERNAL_ERROR"
    SYSTEM_VALIDATION_ERROR = "SYSTEM_VALIDATION_ERROR"
    SYSTEM_RATE_LIMIT = "SYSTEM_RATE_LIMIT"


# ==================== HTTP 状态码映射 ====================
ERROR_STATUS_MAP: dict[ErrorCode, int] = {
    # 400 Bad Request
    ErrorCode.AUTH_INVALID_CREDENTIALS: status.HTTP_400_BAD_REQUEST,
    ErrorCode.AUTH_INVALID_TOKEN: status.HTTP_400_BAD_REQUEST,
    ErrorCode.AUTH_INACTIVE_USER: status.HTTP_400_BAD_REQUEST,
    ErrorCode.USER_INVALID_PASSWORD: status.HTTP_400_BAD_REQUEST,
    ErrorCode.USER_PASSWORD_SAME_AS_OLD: status.HTTP_400_BAD_REQUEST,
    ErrorCode.SYSTEM_VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
    
    # 401 Unauthorized
    ErrorCode.AUTH_EXPIRED_TOKEN: status.HTTP_401_UNAUTHORIZED,
    
    # 403 Forbidden
    ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: status.HTTP_403_FORBIDDEN,
    ErrorCode.AUTH_MISSING_SCOPE: status.HTTP_403_FORBIDDEN,
    ErrorCode.USER_CANNOT_DELETE_SELF: status.HTTP_403_FORBIDDEN,
    ErrorCode.USER_CANNOT_DELETE_SUPERUSER: status.HTTP_403_FORBIDDEN,
    ErrorCode.ITEM_NOT_OWNER: status.HTTP_403_FORBIDDEN,
    
    # 404 Not Found
    ErrorCode.USER_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.ITEM_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    
    # 409 Conflict
    ErrorCode.USER_ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    ErrorCode.USER_EMAIL_ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    
    # 429 Too Many Requests
    ErrorCode.SYSTEM_RATE_LIMIT: status.HTTP_429_TOO_MANY_REQUESTS,
    
    # 500 Internal Server Error
    ErrorCode.SYSTEM_INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


# ==================== 默认错误消息 ====================
DEFAULT_ERROR_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.AUTH_INVALID_CREDENTIALS: "Incorrect email or password",
    ErrorCode.AUTH_INVALID_TOKEN: "Invalid token",
    ErrorCode.AUTH_EXPIRED_TOKEN: "Token has expired",
    ErrorCode.AUTH_INACTIVE_USER: "Inactive user",
    ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: "The user doesn't have enough privileges",
    ErrorCode.AUTH_MISSING_SCOPE: "Missing required scope",
    
    ErrorCode.USER_NOT_FOUND: "User not found",
    ErrorCode.USER_ALREADY_EXISTS: "User already exists",
    ErrorCode.USER_EMAIL_ALREADY_EXISTS: "User with this email already exists",
    ErrorCode.USER_INVALID_PASSWORD: "Incorrect password",
    ErrorCode.USER_PASSWORD_SAME_AS_OLD: "New password cannot be the same as the current one",
    ErrorCode.USER_CANNOT_DELETE_SELF: "Super users are not allowed to delete themselves",
    ErrorCode.USER_CANNOT_DELETE_SUPERUSER: "Cannot delete superuser",
    
    ErrorCode.ITEM_NOT_FOUND: "Item not found",
    ErrorCode.ITEM_NOT_OWNER: "Not enough permissions to access this item",
    
    ErrorCode.SYSTEM_INTERNAL_ERROR: "Internal server error",
    ErrorCode.SYSTEM_VALIDATION_ERROR: "Validation error",
    ErrorCode.SYSTEM_RATE_LIMIT: "Too many requests",
}


class BusinessException(HTTPException):
    """
    业务异常基类
    
    统一所有业务异常，确保返回格式一致:
    {
        "detail": "错误消息",
        "code": "ERROR_CODE",
        "data": {}  // 可选的额外数据
    }
    """
    
    def __init__(
        self,
        code: ErrorCode,
        detail: str | None = None,
        headers: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ):
        self.code = code
        self.data = data or {}
        
        # 获取状态码
        status_code = ERROR_STATUS_MAP.get(code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 获取错误消息
        message = detail or DEFAULT_ERROR_MESSAGES.get(code, "Unknown error")
        
        super().__init__(status_code=status_code, detail=message, headers=headers)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式，用于响应"""
        result = {
            "detail": self.detail,
            "code": self.code.value,
        }
        if self.data:
            result["data"] = self.data
        return result


# ==================== 便捷工厂函数 ====================

def raise_auth_error(
    code: ErrorCode = ErrorCode.AUTH_INVALID_CREDENTIALS,
    detail: str | None = None,
) -> None:
    """抛出认证错误"""
    raise BusinessException(code=code, detail=detail)


def raise_user_not_found(detail: str | None = None) -> None:
    """抛出用户不存在错误"""
    raise BusinessException(code=ErrorCode.USER_NOT_FOUND, detail=detail)


def raise_user_already_exists(detail: str | None = None) -> None:
    """抛出用户已存在错误"""
    raise BusinessException(
        code=ErrorCode.USER_EMAIL_ALREADY_EXISTS,
        detail=detail,
    )


def raise_item_not_found(detail: str | None = None) -> None:
    """抛出物品不存在错误"""
    raise BusinessException(code=ErrorCode.ITEM_NOT_FOUND, detail=detail)


def raise_permission_denied(detail: str | None = None) -> None:
    """抛出权限不足错误"""
    raise BusinessException(
        code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
        detail=detail,
    )


def raise_scope_missing(scope: str | None = None) -> None:
    """抛出缺少 Scope 错误"""
    data = {"required_scope": scope} if scope else None
    raise BusinessException(
        code=ErrorCode.AUTH_MISSING_SCOPE,
        data=data,
    )
