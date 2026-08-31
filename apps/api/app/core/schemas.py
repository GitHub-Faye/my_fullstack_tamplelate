"""
通用 Schema / DTO 定义模块

定义跨领域共享的 API 请求/响应模型，确保契约一致性。
"""

from typing import Generic, TypeVar

from pydantic import field_validator
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

    @field_validator("page")
    @classmethod
    def _clamp_page(cls, v: int) -> int:
        return max(v, 1)

    @field_validator("page_size")
    @classmethod
    def _clamp_page_size(cls, v: int) -> int:
        return max(1, min(v, 100))

    @property
    def offset(self) -> int:
        """计算数据库 offset"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """返回 limit (即 page_size)"""
        return self.page_size
