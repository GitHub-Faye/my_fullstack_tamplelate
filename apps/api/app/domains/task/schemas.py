"""
Task 模块数据传输对象（DTO）定义

定义任务相关的 API 请求和响应模型。
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.models import TaskStatus, TaskType
from app.core.schemas import Message, PaginatedResponse


# ==================== 任务基础模型 ====================

class TaskBase(SQLModel):
    """任务基础属性"""
    name: str = Field(min_length=1, max_length=255, description="任务名称")
    description: Optional[str] = Field(default=None, max_length=2000, description="任务描述")
    task_type: TaskType = Field(default=TaskType.NORMAL, description="任务类型")


# ==================== API 请求模型（Request DTO） ====================

class TaskCreate(TaskBase):
    """创建任务请求"""
    pass


class TaskUpdate(SQLModel):
    """更新任务请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="任务名称")
    description: Optional[str] = Field(default=None, max_length=2000, description="任务描述")
    task_type: Optional[TaskType] = Field(default=None, description="任务类型")


# ==================== API 响应模型（Response DTO） ====================

class TaskPublic(TaskBase):
    """返回给客户端的任务信息"""
    id: uuid.UUID
    pm_id: uuid.UUID
    engineer_id: Optional[uuid.UUID] = None
    status: TaskStatus
    bidding_deadline: Optional[datetime] = None
    T_reported: Optional[float] = None
    T_actual: Optional[float] = None
    progress: Optional[str] = None
    expected_online_time: Optional[datetime] = None
    T_reported_complete_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TasksPublic(PaginatedResponse[TaskPublic]):
    """任务列表分页响应"""
    pass


# ==================== 通用 DTO ====================

# Message 从 app.core.schemas 导入