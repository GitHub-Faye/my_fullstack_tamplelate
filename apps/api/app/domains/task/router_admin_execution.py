"""
任务管理端点模块（管理员改派和暂停审批）

提供管理员操作任务相关的 RESTful API 端点：
- 审批暂停
- 改派任务
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    get_user_scopes,
)
from app.core.scopes import TaskScope
from app.core.errors import BusinessException, ErrorCode, raise_task_not_found
from app.core.schemas import Message
from app.core.models import Task, TaskStatus, UserRoleType

from app.domains.task import repository
from app.domains.task.schemas import TaskPublic
from app.domains.task.schemas_execution import TaskReassignRequest


router = APIRouter()


# ==================== 管理员端点：暂停审批和改派 ====================


@router.post(
    "/{task_id}/pause-approve",
    response_model=TaskPublic,
    summary="审批暂停（管理员）",
    description="管理员审批确认任务暂停"
)
async def pause_approve_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> Any:
    """
    审批暂停任务

    权限：管理员或超管

    业务流程：
    1. 检查任务是否存在
    2. 检查权限（管理员）
    3. 检查状态（必须是 PAUSED）
    4. 确认暂停（状态保持 PAUSED）
    """
    # 1. 查询任务
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 2. 检查权限（管理员）
    user_scopes = await get_user_scopes(session, current_user)
    if TaskScope.ADMIN.value not in user_scopes:
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="Only admin can perform this action"
        )

    # 3. 检查状态
    if task.status != TaskStatus.PAUSED:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Task status must be 'paused', current status is '{task.status.value}'"
        )

    # 4. 确认暂停（状态保持，可添加审计日志）
    # 当前仅确认状态，可扩展：记录审批时间、审批人等
    return task


@router.post(
    "/{task_id}/reassign",
    response_model=TaskPublic,
    summary="改派任务（管理员）",
    description="管理员将任务改派给其他工程师，状态变为待开工"
)
async def reassign_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    request: TaskReassignRequest,
) -> Any:
    """
    改派任务

    权限：管理员或超管

    业务流程：
    1. 检查任务是否存在
    2. 检查权限（管理员）
    3. 检查新工程师是否存在且是工程师角色
    4. 更新 engineer_id，状态变为 PENDING_START
    """
    # 1. 查询任务
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 2. 检查权限（管理员）
    user_scopes = await get_user_scopes(session, current_user)
    if TaskScope.ADMIN.value not in user_scopes:
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="Only admin can perform this action"
        )

    # 3. 检查新工程师是否存在
    from app.core.models import User
    new_engineer = await session.get(User, request.new_engineer_id)
    if not new_engineer:
        raise BusinessException(
            code=ErrorCode.USER_NOT_FOUND,
            detail=f"Engineer with id {request.new_engineer_id} not found"
        )

    # 检查新工程师是否是工程师角色
    if new_engineer.role != UserRoleType.ENGINEER:
        raise BusinessException(
            code=ErrorCode.USER_ROLE_MISMATCH,
            detail="Target user is not an engineer"
        )

    # 4. 更新任务
    task.engineer_id = request.new_engineer_id
    task.status = TaskStatus.PENDING_START
    session.add(task)
    await session.commit()
    await session.refresh(task)

    return task
