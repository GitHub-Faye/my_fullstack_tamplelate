"""
审计日志模块 — 业务服务层

统一审计日志的创建入口，自动处理 ip_address 等通用字段。
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
    target_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    """
    统一创建审计日志入口。

    封装 repository 层的 create_audit_log，将来可在此处扩展
    异步写入、日志队列、通知等能力。

    Args:
        session: 数据库会话
        user_id: 操作人 ID
        action: 操作类型（如 task.create, user.toggle_active）
        target_type: 操作对象类型（如 task, user, system_rule）
        target_id: 操作对象 ID（可选）
        details: 操作详情 JSON 字符串（可选）
        ip_address: 操作人 IP 地址（可选，由调用方传入 request.client.host）
    """
    await repo_create_audit_log(
        session=session,
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )