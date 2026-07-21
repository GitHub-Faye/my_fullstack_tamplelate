"""
审计日志模块 — API 路由

提供统一的审计日志查询端点，所有角色可通过此接口查看操作日志，
权限规则：管理员可查全量，市场产品PM/工程师只能查自己的操作。
"""

import uuid
from typing import Annotated, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
)
from app.core.models import UserRoleType
from app.domains.audit.schemas import AuditLogList
from app.domains.audit import repository

router = APIRouter()


@router.get(
    "/",
    response_model=AuditLogList,
    summary="查看操作日志",
    description="查看系统操作审计日志。管理员可查全量，市场产品PM/工程师仅查看自己的操作。",
)
async def read_audit_logs(
    session: SessionDep,
    current_user: CurrentUser,
    request: Request,
    target_type: Annotated[Optional[str], Query(description="按目标类型过滤（如 task, user, system_rule）")] = None,
    action: Annotated[Optional[str], Query(description="按操作类型过滤（如 task.create, user.toggle_active）")] = None,
    user_id: Annotated[Optional[uuid.UUID], Query(description="按操作人 ID 过滤（仅管理员可用）")] = None,
    start_time: Annotated[Optional[str], Query(description="开始时间（ISO 格式）")] = None,
    end_time: Annotated[Optional[str], Query(description="结束时间（ISO 格式）")] = None,
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
    resolved_user_id: Optional[uuid.UUID] = None
    if current_user.role != UserRoleType.ADMIN:
        resolved_user_id = current_user.id
    elif user_id:
        resolved_user_id = user_id

    # 解析时间范围
    start_dt: Optional[datetime] = None
    if start_time:
        start_dt = datetime.fromisoformat(start_time)
    end_dt: Optional[datetime] = None
    if end_time:
        end_dt = datetime.fromisoformat(end_time)

    offset = (page - 1) * page_size

    logs, count = await repository.get_audit_logs(
        session=session,
        skip=offset,
        limit=page_size,
        target_type=target_type,
        user_id=resolved_user_id,
        action=action,
        start_time=start_dt,
        end_time=end_dt,
    )

    return AuditLogList(
        data=logs,
        count=count,
        page=page,
        page_size=page_size,
        total_pages=(count + page_size - 1) // page_size if count > 0 else 0,
    )