"""
任务执行 API 端点模块

提供工程师执行任务相关的 RESTful API 端点：
- 启动任务
- 拒绝任务
- 申请暂停
- 恢复任务
- 完成任务
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, SessionDep
from app.core.errors import BusinessException, ErrorCode, raise_task_not_found
from app.core.schemas import Message
from app.core.models import Task, TaskStatus, UserRoleType, User

from app.domains.task import repository
from app.domains.task.schemas import TaskPublic
from app.domains.task.schemas_execution import (
    TaskStartRequest,
    TaskRejectRequest,
    TaskPauseRequest,
    TaskResumeRequest,
    TaskCompleteRequest,
)


router = APIRouter()


# ==================== 工程师端点：任务执行 ====================


async def check_task_assigned_to_engineer(
    session: SessionDep,
    current_user: CurrentUser,
    task: Task,
) -> None:
    """
    检查任务是否分配给当前工程师

    Args:
        session: 数据库会话
        current_user: 当前用户
        task: 任务对象

    Raises:
        BusinessException: 403 任务未分配给当前工程师
    """
    # Reload user from database to ensure role is loaded
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


async def check_task_status(
    task: Task,
    expected_status: TaskStatus,
) -> None:
    """
    检查任务状态是否符合预期

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


@router.post(
    "/{task_id}/start",
    response_model=TaskPublic,
    summary="启动任务",
    description="工程师启动待开工的任务，状态从 PENDING_START 变为 IN_PROGRESS"
)
async def start_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    request: TaskStartRequest = None,
) -> Any:
    """
    启动任务

    权限：被分配的工程师

    业务流程：
    1. 检查任务是否存在
    2. 检查权限（被分配的工程师）
    3. 检查状态（必须是 PENDING_START）
    4. 更新状态为 IN_PROGRESS
    """
    # 1. 查询任务
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 2. 检查权限（被分配的工程师）
    await check_task_assigned_to_engineer(session, current_user, task)

    # 3. 检查状态
    await check_task_status(task, TaskStatus.PENDING_START)

    # 4. 更新状态
    task.status = TaskStatus.IN_PROGRESS
    session.add(task)
    await session.commit()
    await session.refresh(task)

    return task


@router.post(
    "/{task_id}/reject",
    response_model=TaskPublic,
    summary="拒绝任务",
    description="工程师拒绝待开工的任务，任务回退到已确认未发布状态"
)
async def reject_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    request: TaskRejectRequest = None,
) -> Any:
    """
    拒绝任务

    权限：被分配的工程师

    业务流程：
    1. 检查任务是否存在
    2. 检查权限（被分配的工程师）
    3. 检查状态（必须是 PENDING_START）
    4. 更新状态为 CONFIRMED_UNPUBLISHED，清空 engineer_id
    """
    # 1. 查询任务
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 2. 检查权限（被分配的工程师）
    await check_task_assigned_to_engineer(session, current_user, task)

    # 3. 检查状态
    await check_task_status(task, TaskStatus.PENDING_START)

    # 4. 更新状态
    task.status = TaskStatus.CONFIRMED_UNPUBLISHED
    task.engineer_id = None
    session.add(task)
    await session.commit()
    await session.refresh(task)

    return task


@router.post(
    "/{task_id}/pause-request",
    response_model=TaskPublic,
    summary="申请暂停",
    description="工程师申请暂停正在进行的任务"
)
async def pause_request_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    request: TaskPauseRequest = None,
) -> Any:
    """
    申请暂停任务

    权限：被分配的工程师

    业务流程：
    1. 检查任务是否存在
    2. 检查权限（被分配的工程师）
    3. 检查状态（必须是 IN_PROGRESS）
    4. 更新状态为 PAUSED
    """
    # 1. 查询任务
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 2. 检查权限（被分配的工程师）
    await check_task_assigned_to_engineer(session, current_user, task)

    # 3. 检查状态
    await check_task_status(task, TaskStatus.IN_PROGRESS)

    # 4. 更新状态
    task.status = TaskStatus.PAUSED
    session.add(task)
    await session.commit()
    await session.refresh(task)

    return task


@router.post(
    "/{task_id}/resume",
    response_model=TaskPublic,
    summary="恢复任务",
    description="工程师恢复暂停的任务"
)
async def resume_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    request: TaskResumeRequest = None,
) -> Any:
    """
    恢复任务

    权限：被分配的工程师

    业务流程：
    1. 检查任务是否存在
    2. 检查权限（被分配的工程师）
    3. 检查状态（必须是 PAUSED）
    4. 更新状态为 IN_PROGRESS
    """
    # 1. 查询任务
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 2. 检查权限（被分配的工程师）
    await check_task_assigned_to_engineer(session, current_user, task)

    # 3. 检查状态
    await check_task_status(task, TaskStatus.PAUSED)

    # 4. 更新状态
    task.status = TaskStatus.IN_PROGRESS
    session.add(task)
    await session.commit()
    await session.refresh(task)

    return task


@router.post(
    "/{task_id}/complete",
    response_model=TaskPublic,
    summary="完成任务",
    description="工程师标记任务完成，填写实际工时"
)
async def complete_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    request: TaskCompleteRequest,
) -> Any:
    """
    完成任务

    权限：被分配的工程师

    业务流程：
    1. 检查任务是否存在
    2. 检查权限（被分配的工程师）
    3. 检查状态（必须是 IN_PROGRESS）
    4. 更新状态为 COMPLETED，记录工时
    """
    # 1. 查询任务
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 2. 检查权限（被分配的工程师）
    await check_task_assigned_to_engineer(session, current_user, task)

    # 3. 检查状态
    await check_task_status(task, TaskStatus.IN_PROGRESS)

    # 4. 更新状态和工时
    task.status = TaskStatus.COMPLETED
    task.T_reported = request.T_reported
    session.add(task)
    await session.commit()
    await session.refresh(task)

    return task