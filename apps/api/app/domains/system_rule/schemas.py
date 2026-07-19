"""
系统规则模块数据传输对象（DTO）定义

定义规则配置相关的 API 请求和响应模型。
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.models import RuleCategory
from app.core.schemas import PaginatedResponse


# ==================== API 请求模型 ====================

class SystemRuleCreate(SQLModel):
    """创建规则请求"""
    category: RuleCategory = Field(description="规则分类")
    name: str = Field(max_length=100, description="规则名称")
    applies_to: Optional[str] = Field(default=None, max_length=50, description="适用对象（如角色类型）")
    value: str = Field(max_length=500, description="规则值（JSON 或数值）")
    is_public: bool = Field(default=False, description="是否对员工公开")
    is_active: bool = Field(default=True, description="是否启用")


class SystemRuleUpdate(SQLModel):
    """更新规则请求"""
    category: Optional[RuleCategory] = Field(default=None, description="规则分类")
    name: Optional[str] = Field(default=None, max_length=100, description="规则名称")
    applies_to: Optional[str] = Field(default=None, max_length=50, description="适用对象")
    value: Optional[str] = Field(default=None, max_length=500, description="规则值")
    is_public: Optional[bool] = Field(default=None, description="是否对员工公开")
    is_active: Optional[bool] = Field(default=None, description="是否启用")


# ==================== API 响应模型 ====================

class SystemRulePublic(SQLModel):
    """规则公开信息"""
    id: uuid.UUID
    category: RuleCategory
    name: str
    applies_to: Optional[str] = None
    value: str
    is_public: bool
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SystemRulesPublic(PaginatedResponse[SystemRulePublic]):
    """规则列表"""
    pass