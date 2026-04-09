import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.core.schemas import Message, PaginatedResponse


# --------------------------------- 物品模型 ---------------------------------------------
# 共享属性
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)

# --------------------------- API 请求模型（Request DTO） ------------------------------------
# 创建 Item DTO
class ItemCreate(ItemBase):
    pass


# 更新 Item DTO，title 可选
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# ---------------------------- API 响应模型（Response DTO） --------------------------------
# 返回给客户端的 Item 信息
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


# 使用统一分页协议
class ItemsPublic(PaginatedResponse[ItemPublic]):
    pass


# ---------------------------- 通用 DTO --------------------------------------------------
# Message 从 app.core.schemas 导入

