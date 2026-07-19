"""
Task 模块权限检查依赖

提供任务相关的权限检查函数和共享导入。
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
    require_any_scope,
    get_user_scopes,
)
from app.core.scopes import TaskScope
from app.core.schemas import Message, PaginationParams
from app.core.errors import (
    BusinessException,
    ErrorCode,
    raise_task_not_found,
    raise_permission_denied,
)
from app.core.models import Task, TaskStatus, TaskType, UserRoleType, User

from app.domains.task import repository
from app.domains.task.schemas import (
    TaskCreate,
    TaskPublic,
    TasksPublic,
    TaskUpdate,
)
from app.domains.task.schemas_execution import (
    TaskStartRequest,
    TaskRejectRequest,
    TaskPauseRequest,
    TaskResumeRequest,
    TaskCompleteRequest,
    TaskReassignRequest,
)
from app.domains.starpoint.calculation import trigger_starpoint_calculation


async def check_task_owner_or_admin(
    session: SessionDep,
    current_user: CurrentUser,
    task_pm_id: uuid.UUID,
) -> bool:
    """
    检查用户是否是任务的所有者（PM）或拥有管理权限

    Args:
        session: 数据库会话
        current_user: 当前用户
        task_pm_id: 任务的 PM ID

    Returns:
        是否有权限

    Raises:
        BusinessException: 403 无权限
    """
    # 是自己的任务
    if task_pm_id == current_user.id:
        return True

    # 检查是否有 task:admin 权限
    user_scopes = await get_user_scopes(session, current_user)
    if TaskScope.ADMIN.value in user_scopes:
        return True

    raise_permission_denied("Not enough permissions")


async def check_task_status_editable(
    session: SessionDep,
    current_user: CurrentUser,
    task: Task,
) -> bool:
    """
    检查任务是否可编辑（仅"未确认"状态）

    Args:
        session: 数据库会话
        current_user: 当前用户
        task: 任务对象

    Returns:
        是否可编辑

    Raises:
        BusinessException: 400 任务状态不可编辑
    """
    if task.status != TaskStatus.UNCONFIRMED:
        from app.core.errors import BusinessException, ErrorCode
        raise BusinessException(
            code=ErrorCode.SYSTEM_VALIDATION_ERROR,
            detail=f"Task status '{task.status.value}' cannot be edited. Only 'unconfirmed' tasks can be modified."
        )

    return True


async def check_task_status(
    task: Task,
    expected_status: TaskStatus,
) -> None:
    """
    检查任务状态是否符合预期。

    Args:
        task: 任务对象
        expected_status: 期望的状态

    Raises:
        BusinessException: 400 任务状态不符合要求
    """
    if task.status != expected_status:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Task status must be '{expected_status.value}', current status is '{task.status.value}'"
        )


async def check_task_assigned_to_engineer(
    session: SessionDep,
    current_user: CurrentUser,
    task: Task,
) -> None:
    """
    检查任务是否分配给当前工程师。

    Args:
        session: 数据库会话
        current_user: 当前用户
        task: 任务对象

    Raises:
        BusinessException: 403 任务未分配给当前工程师
    """
    from sqlalchemy import select
    stmt = select(User).where(User.id == current_user.id)
    result = await session.execute(stmt)
    user_with_role = result.scalar_one_or_none()

    if not user_with_role or user_with_role.role != UserRoleType.ENGINEER:
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="Only engineers can perform this action"
        )

    if task.engineer_id != current_user.id:
        raise BusinessException(
            code=ErrorCode.TASK_NOT_ASSIGNED_TO_USER,
            detail="Task is not assigned to you"
        )


async def check_admin_scope(
    session: SessionDep,
    current_user: CurrentUser,
) -> None:
    """
    检查用户是否有 task:admin scope。

    Args:
        session: 数据库会话
        current_user: 当前用户

    Raises:
        BusinessException: 403 无管理权限
    """
    user_scopes = await get_user_scopes(session, current_user)
    if TaskScope.ADMIN.value not in user_scopes:
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="Only admin can perform this action"
        )


async def check_pm_role(
    session: SessionDep,
    current_user: CurrentUser,
) -> bool:
    """
    检查用户是否是 PM 角色

    Args:
        session: 数据库会话
        current_user: 当前用户

    Returns:
        是否是 PM

    Raises:
        BusinessException: 403 无权限
    """
    from app.core.models import UserRoleType

    if current_user.role != UserRoleType.PM:
        raise_permission_denied("Only PM can perform this action")

    return True