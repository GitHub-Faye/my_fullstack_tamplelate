"""
角色管理模块 — Schema 定义

提供角色管理的请求/响应 DTO：
- RoleCreate: 创建角色
- RoleUpdate: 更新角色
- RolePublic: 角色详情（含 scopes 列表）
- RolesPublic: 分页角色列表
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.schemas import PaginatedResponse


class RoleCreate(SQLModel):
    """创建角色请求"""
    name: str = Field(min_length=1, max_length=50, description="角色名称")
    scopes: list[str] = Field(default=[], description="权限范围列表")


class RoleUpdate(SQLModel):
    """更新角色请求"""
    name: str | None = Field(default=None, min_length=1, max_length=50, description="角色名称")
    scopes: list[str] | None = Field(default=None, description="权限范围列表（替换全部）")


class RolePublic(SQLModel):
    """角色详情响应"""
    id: uuid.UUID
    name: str
    scopes: list[str] = []
    created_at: datetime | None = None


class RolesPublic(PaginatedResponse[RolePublic]):
    pass