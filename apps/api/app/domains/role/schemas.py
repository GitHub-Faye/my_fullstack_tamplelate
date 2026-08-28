"""
Role 领域 Schema / DTO 定义模块

定义 Role 的 API 请求/响应模型：
- RoleCreate: 创建角色的请求 DTO（name 必填，scopes 可选）
- RoleUpdate: 更新角色的请求 DTO（所有字段可选，支持部分更新）
- RolePublic: 单条角色的响应 DTO（含 scopes 列表）
- RolesPublic: 角色分页列表的响应 DTO

说明：
- 角色与 scope 是多对多关系（RoleScope 关联表），
  角色的 scope 集合在响应中统一以 list[str] 返回。
- scopes 合法性由 repository 层使用 app.core.scopes.ALL_SCOPES 校验，
  保证写入的 scope 一定在系统定义范围内。
"""

import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field

from app.core.schemas import PaginatedResponse


# --------------------------- API 请求模型（Request DTO） ------------------------------------
class RoleCreate(SQLModel):
    """创建角色的请求体：name 必填，scopes 可选（默认空集合）"""
    name: str = Field(min_length=1, max_length=50)
    scopes: list[str] = Field(default_factory=list, max_length=100)


class RoleUpdate(SQLModel):
    """更新角色的请求体：所有字段可选，未设置的字段保持不变（部分更新）

    - name：角色名（更新后会影响引用此角色的用户）
    - scopes：完整的 scope 集合（整体替换，非增量合并）
    """
    name: str | None = Field(default=None, min_length=1, max_length=50)
    scopes: list[str] | None = Field(default=None, max_length=100)


# ---------------------------- API 响应模型（Response DTO） --------------------------------
class RolePublic(SQLModel):
    """单条角色的响应体：基础字段 + 当前持有的 scope 列表"""
    id: uuid.UUID
    name: str
    created_at: datetime | None = None
    scopes: list[str] = []


class RolesPublic(PaginatedResponse[RolePublic]):
    """角色分页列表的响应体：data / count / page / page_size / total_pages"""
    pass
