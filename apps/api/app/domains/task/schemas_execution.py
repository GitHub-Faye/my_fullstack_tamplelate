"""
任务执行相关的请求和响应模型
"""

import uuid
from typing import Optional

from sqlmodel import Field, SQLModel


class TaskStartRequest(SQLModel):
    """启动任务请求"""
    pass


class TaskRejectRequest(SQLModel):
    """拒绝任务请求"""
    reason: Optional[str] = Field(default=None, max_length=500, description="拒绝原因")


class TaskPauseRequest(SQLModel):
    """申请暂停请求"""
    reason: Optional[str] = Field(default=None, max_length=500, description="暂停原因")


class TaskResumeRequest(SQLModel):
    """恢复任务请求"""
    pass


class TaskCompleteRequest(SQLModel):
    """完成任务请求"""
    T_reported: float = Field(ge=0, description="工程师填报工时（小时）")


class TaskReassignRequest(SQLModel):
    """改派任务请求"""
    new_engineer_id: uuid.UUID = Field(description="新工程师ID")
