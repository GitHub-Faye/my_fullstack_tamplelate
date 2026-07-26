"""
审计日志模块 — 数据访问层

提供审计日志的创建和查询功能。
"""
import uuid
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import AuditLog, User
from app.core.db_utils import paginated_query


async def create_audit_log(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    action: str,
    target_type: str,
    target_id: str | None = None,
    details: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """创建操作审计日志"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def get_audit_logs(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    target_type: str | None = None,
    target_id: str | None = None,
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> Tuple[list[AuditLog], int]:
    """获取操作审计日志列表（分页），支持多条件筛选和 user_name 填充"""
    conditions = []
    if target_type:
        conditions.append(AuditLog.target_type == target_type)
    if target_id:
        conditions.append(AuditLog.target_id == target_id)
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if action:
        conditions.append(AuditLog.action == action)
    if start_time:
        conditions.append(AuditLog.created_at >= start_time)
    if end_time:
        conditions.append(AuditLog.created_at <= end_time)

    tasks, count = await paginated_query(
        session=session,
        model=AuditLog,
        skip=skip,
        limit=limit,
        conditions=conditions if conditions else None,
        order_by=AuditLog.created_at.desc(),
        eager_load_relations=[AuditLog.operator],
    )

    return tasks, count


async def get_affected_user_name(
    session: AsyncSession,
    target_type: str | None,
    target_id: str | None,
) -> str | None:
    """根据 target_type 和 target_id 获取影响人姓名"""
    if target_type != "user" or not target_id:
        return None
    try:
        user_uuid = uuid.UUID(target_id)
    except (ValueError, TypeError):
        return None
    stmt = select(User).where(User.id == user_uuid)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return user.full_name or str(user.id)[:8]
    return None