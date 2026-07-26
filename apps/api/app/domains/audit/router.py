"""
审计日志模块 — API 路由

提供统一的审计日志查询端点，所有角色可通过此接口查看操作日志，
权限规则：管理员可查全量，市场产品PM/工程师只能查自己的操作。
"""

import uuid
from typing import Annotated, Any
from datetime import datetime

from fastapi import APIRouter, Query
from fastapi.exceptions import RequestValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
)
from app.core.models import UserRoleType, User
from app.domains.audit.schemas import AuditLogList, AuditLogPublic
from app.domains.audit import repository

router = APIRouter()


def _parse_iso_datetime(value: str | None, param_name: str) -> datetime | None:
    """解析 ISO 格式时间字符串，非法输入返回 422 而非 500。"""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        raise RequestValidationError([
            {
                "loc": ["query", param_name],
                "msg": "Invalid ISO datetime format",
                "type": "value_error",
            }
        ])


async def _batch_fetch_affected_names(
    session: AsyncSession,
    logs: list,
) -> dict[str, str | None]:
    """批量查询 target_type="user" 的 target_id 对应的 full_name"""
    user_ids = set()
    for log in logs:
        if log.target_type == "user" and log.target_id:
            try:
                user_ids.add(uuid.UUID(log.target_id))
            except (ValueError, TypeError):
                pass
    if not user_ids:
        return {}

    stmt = select(User).where(User.id.in_(user_ids))
    result = await session.execute(stmt)
    users = result.scalars().all()
    return {str(u.id): u.full_name or str(u.id)[:8] for u in users}


@router.get(
    "/",
    response_model=AuditLogList,
    summary="查看操作日志",
    description="查看系统操作审计日志。管理员可查全量，市场产品PM/工程师仅查看自己的操作。",
)
async def read_audit_logs(
    session: SessionDep,
    current_user: CurrentUser,
    target_type: Annotated[str | None, Query(description="按目标类型过滤（如 task, user, system_rule）")] = None,
    target_id: Annotated[str | None, Query(description="按目标 ID 过滤")] = None,
    action: Annotated[str | None, Query(description="按操作类型过滤（如 task.create, user.toggle_active）")] = None,
    user_id: Annotated[uuid.UUID | None, Query(description="按操作人 ID 过滤（仅管理员可用）")] = None,
    start_time: Annotated[str | None, Query(description="开始时间（ISO 格式）")] = None,
    end_time: Annotated[str | None, Query(description="结束时间（ISO 格式）")] = None,
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量，默认20，最大100")] = 20,
) -> Any:
    """
    获取操作日志列表（分页）。

    权限规则：
    - 管理员可查看所有日志，可传任意筛选参数
    - 市场产品PM 和工程师只能查看自己的操作（user_id 强制为当前用户）
    """
    # 权限控制：非管理员只能查自己的
    resolved_user_id: uuid.UUID | None = None
    if current_user.role != UserRoleType.ADMIN:
        resolved_user_id = current_user.id
    elif user_id:
        resolved_user_id = user_id

    # 解析时间范围
    start_dt = _parse_iso_datetime(start_time, "start_time")
    end_dt = _parse_iso_datetime(end_time, "end_time")

    offset = (page - 1) * page_size

    logs, count = await repository.get_audit_logs(
        session=session,
        skip=offset,
        limit=page_size,
        target_type=target_type,
        target_id=target_id,
        user_id=resolved_user_id,
        action=action,
        start_time=start_dt,
        end_time=end_dt,
    )

    # 批量查询影响人姓名
    affected_names = await _batch_fetch_affected_names(session, logs)

    # 将 AuditLog ORM 对象转换为 AuditLogPublic schema
    data = []
    for log in logs:
        affected_name = None
        if log.target_type == "user" and log.target_id:
            affected_name = affected_names.get(log.target_id)

        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at,
            "operator_name": log.operator_name,
            "affected_name": affected_name,
        }
        data.append(AuditLogPublic(**log_dict))

    return AuditLogList(
        data=data,
        count=count,
        page=page,
        page_size=page_size,
        total_pages=(count + page_size - 1) // page_size if count > 0 else 0,
    )