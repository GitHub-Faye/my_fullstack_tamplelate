"""
审计日志模块 — 业务服务层

统一审计日志的创建入口。
"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.audit.repository import create_audit_log as repo_create_audit_log


async def create_audit_log(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    action: str,
    target_type: str,
    target_id: str | None = None,
    details: str | None = None,
    ip_address: str | None = None,
) -> None:
    """统一创建审计日志入口，委托给 repository 层写入数据库。"""
    await repo_create_audit_log(
        session=session,
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )