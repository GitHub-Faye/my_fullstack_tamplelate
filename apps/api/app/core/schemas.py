"""
通用 Schema / DTO 定义模块

定义跨领域共享的 API 请求/响应模型，确保契约一致性。
"""

from typing import Any, Generic, TypeVar

from sqlmodel import SQLModel


# ==================== 通用消息响应 ====================

class Message(SQLModel):
    """通用消息响应"""
    message: str


# ==================== 统一分页协议 ====================

T = TypeVar("T")


class PaginatedResponse(SQLModel, Generic[T]):
    """
    统一分页响应格式
    
    所有列表查询接口统一使用此格式返回:
    {
        "data": [...],      // 数据列表
        "count": 100,       // 总记录数
        "page": 1,          // 当前页码 (可选)
        "page_size": 20,    // 每页大小 (可选)
        "total_pages": 5    // 总页数 (可选)
    }
    """
    data: list[T]
    count: int
    page: int | None = None
    page_size: int | None = None
    total_pages: int | None = None


class PaginationParams(SQLModel):
    """
    分页查询参数
    
    用于统一分页请求参数:
    - page: 页码，从 1 开始
    - page_size: 每页数量，默认 20，最大 100
    """
    page: int = 1
    page_size: int = 20
    
    def __init__(self, **data):
        super().__init__(**data)
        # 确保 page 至少为 1
        if self.page < 1:
            self.page = 1
        # 限制 page_size 范围
        if self.page_size < 1:
            self.page_size = 1
        elif self.page_size > 100:
            self.page_size = 100
    
    @property
    def offset(self) -> int:
        """计算数据库 offset"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """返回 limit (即 page_size)"""
        return self.page_size


# ==================== 通用错误响应 ====================

class ErrorDetail(SQLModel):
    """错误详情"""
    loc: list[str] | None = None  # 错误位置，如 ["body", "email"]
    msg: str  # 错误消息
    type: str | None = None  # 错误类型


class ErrorResponse(SQLModel):
    """
    统一错误响应格式
    
    {
        "detail": "错误消息" | [{"loc": [...], "msg": "...", "type": "..."}],
        "code": "ERROR_CODE",
        "data": {}  // 额外数据
    }
    """
    detail: str | list[ErrorDetail]
    code: str | None = None
    data: dict[str, Any] | None = None


# ==================== 通用 ID 参数 ====================

class IDParam(SQLModel):
    """通用 ID 参数"""
    id: str


# ==================== 批量操作 ====================

class BulkOperationResult(SQLModel):
    """批量操作结果"""
    success_count: int
    failed_count: int
    errors: list[dict[str, Any]] | None = None
