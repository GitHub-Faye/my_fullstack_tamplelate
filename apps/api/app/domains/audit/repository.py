"""
审计日志模块 — 数据访问层

提供审计日志的创建和查询功能。
"""
import uuid
from typing import Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import AuditLog
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
    user_id: uuid.UUID | None = None,
) -> Tuple[list[AuditLog], int]:
    """获取操作审计日志列表（分页）"""
    from sqlalchemy import and_

    conditions = []
    if target_type:
        conditions.append(AuditLog.target_type == target_type)
    if user_id:
        conditions.append(AuditLog.user_id == user_id)

    return await paginated_query(
        session=session,
        model=AuditLog,
        skip=skip,
        limit=limit,
        conditions=conditions if conditions else None,
        order_by=AuditLog.created_at.desc(),
    )