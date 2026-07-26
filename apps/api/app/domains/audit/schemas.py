"""
审计日志模块 — Schema 定义

提供审计日志的公有 DTO：
- AuditLogPublic: 单个审计日志
- AuditLogList: 分页审计日志列表
"""
import uuid
from datetime import datetime

from sqlmodel import SQLModel

from app.core.schemas import PaginatedResponse


class AuditLogPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    target_type: str
    target_id: str | None = None
    details: str | None = None
    ip_address: str | None = None
    created_at: datetime | None = None
    operator_name: str | None = None
    affected_name: str | None = None  # 影响人姓名（仅 target_type="user" 时有值）


class AuditLogList(PaginatedResponse[AuditLogPublic]):
    pass