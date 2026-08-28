"""
Item 领域 Schema / DTO 定义模块

定义 Item 的 API 请求/响应模型：
- ItemCreate: 创建 Item 的请求 DTO（title 必填，description 可选）
- ItemUpdate: 更新 Item 的请求 DTO（所有字段可选，支持部分更新）
- ItemPublic: 单条 Item 的响应 DTO
- ItemsPublic: Item 分页列表的响应 DTO

说明：
- 共享字段 title/description 的单一来源是 app.core.models.ItemBase，
  此处直接复用，避免在多个文件中重复定义导致字段漂移。
- ItemUpdate 不继承 ItemBase：因为其字段全部可选（父类必填），
  独立声明既能复用约束，又避免了用 type: ignore 覆盖父类字段的反模式。
"""

import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field

from app.core.models import ItemBase
from app.core.schemas import PaginatedResponse


# --------------------------- API 请求模型（Request DTO） ------------------------------------
class ItemCreate(ItemBase):
    """创建 Item 的请求体：与 ItemBase 字段一致（title 必填、description 可选）"""
    pass


class ItemUpdate(SQLModel):
    """更新 Item 的请求体：所有字段可选，未设置的字段保持不变（部分更新）"""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# ---------------------------- API 响应模型（Response DTO） --------------------------------
class ItemPublic(ItemBase):
    """单条 Item 的响应体：在共享字段基础上附加数据库生成的字段（id / owner_id / created_at）"""
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(PaginatedResponse[ItemPublic]):
    """Item 分页列表的响应体：data / count / page / page_size / total_pages"""
    pass