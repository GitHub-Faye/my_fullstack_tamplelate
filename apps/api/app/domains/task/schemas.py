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
    expected_online_time: Optional[datetime] = Field(default=None, description="预期上线时间")


# ==================== API 请求模型（Request DTO） ====================

class TaskCreate(TaskBase):
    """创建任务请求"""
    pass


class AdminTaskCreate(TaskBase):
    """管理员创建任务请求"""
    engineer_id: uuid.UUID = Field(description="指派工程师 ID")


class TaskUpdate(SQLModel):
    """更新任务请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="任务名称")
    description: Optional[str] = Field(default=None, max_length=2000, description="任务描述")
    task_type: Optional[TaskType] = Field(default=None, description="任务类型")
    expected_online_time: Optional[datetime] = Field(default=None, description="预期上线时间")


# ==================== API 响应模型（Response DTO） ====================

class TaskPublic(TaskBase):
    """返回给客户端的任务信息"""
    id: uuid.UUID
    pm_id: uuid.UUID
    pm_name: str = Field(description="发布任务的PM姓名")
    engineer_id: Optional[uuid.UUID] = None
    engineer_name: Optional[str] = Field(default=None, description="工程师姓名")
    status: TaskStatus
    bidding_deadline: Optional[datetime] = None
    T_reported: Optional[float] = None
    T_actual: Optional[float] = None
    progress: Optional[str] = None
    T_reported_complete_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TasksPublic(PaginatedResponse[TaskPublic]):
    """任务列表分页响应"""
    pass



class TaskStartRequest(SQLModel):
    """启动任务请求"""
    pass


class TaskPauseRequest(SQLModel):
    """申请暂停请求"""
    reason: Optional[str] = Field(default=None, max_length=500, description="暂停原因")


class TaskResumeRequest(SQLModel):
    """恢复任务请求"""
    pass


class TaskCompleteRequest(SQLModel):
    """完成任务请求"""
    pass


class TaskReassignRequest(SQLModel):
    """改派任务请求"""
    new_engineer_id: uuid.UUID = Field(description="新工程师ID")
    T_reported: Optional[float] = Field(default=None, ge=0, description="T报（管理员改派时重新给定）")

# ==================== 通用 DTO ====================

# Message 从 app.core.schemas 导入