"""
Task 模块路由层 — 操作端点

提供管理员审核/发布和工程师执行的 RESTful API 端点：
- 管理员：审核通过/驳回、发布竞价、转换类型、暂停审批/驳回、改派
- 工程师：启动、拒绝、暂停申请、恢复、完成任务
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
)
from app.core.scopes import TaskScope
from app.core.schemas import Message
from app.core.errors import BusinessException, ErrorCode, raise_task_not_found
from app.core.models import Task, TaskStatus, TaskType, UserRoleType, User

from app.domains.task import repository
from app.domains.task.schemas import TaskPublic
from app.domains.task.schemas_execution import (
    TaskCompleteRequest,
    TaskReassignRequest,
)
from app.domains.task.dependencies import (
    check_task_status,
    check_task_assigned_to_engineer,
    check_admin_scope,
    check_task_owner_or_admin,
)
from app.domains.starpoint.calculation import trigger_starpoint_calculation
from app.domains.audit.service import create_audit_log

router = APIRouter()


# ==================== 管理员：审核与发布 ====================


@router.post(
    "/{task_id}/approve",
    response_model=TaskPublic,
    summary="审核通过任务（管理员）",
    description="管理员审核通过任务，状态变为 'confirmed_unpublished'",
)
async def approve_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(TaskScope.APPROVE))],
) -> Any:
    """审核通过任务 — 仅 'unconfirmed' 状态可审核"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    if task.status != TaskStatus.UNCONFIRMED:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Task status '{task.status.value}' cannot be approved."
        )
    task.status = TaskStatus.CONFIRMED_UNPUBLISHED
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.approve",
        target_type="task", target_id=str(task_id),
        details=f"Task approved, status changed to confirmed_unpublished",
        ip_address=None,
    )
    return task


@router.post(
    "/{task_id}/reject",
    response_model=TaskPublic,
    summary="驳回任务（管理员）",
    description="管理员驳回任务，状态保持 'unconfirmed'",
)
async def reject_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(TaskScope.APPROVE))],
) -> Any:
    """驳回任务 — 仅 'unconfirmed' 状态可驳回"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    if task.status != TaskStatus.UNCONFIRMED:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Task status '{task.status.value}' cannot be rejected."
        )
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.reject",
        target_type="task", target_id=str(task_id),
        details=f"Task rejected by admin", ip_address=None,
    )
    return task


@router.post(
    "/{task_id}/publish",
    response_model=TaskPublic,
    summary="发布任务到竞价池（管理员）",
    description="管理员发布任务到竞价池，状态变为 'bidding'",
)
async def publish_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    bidding_days: int = 3,
    _: Annotated[None, Depends(require_scope(TaskScope.APPROVE))],
) -> Any:
    """发布任务到竞价池 — 仅 'confirmed_unpublished' 状态可发布"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    if task.status != TaskStatus.CONFIRMED_UNPUBLISHED:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Task status '{task.status.value}' cannot be published."
        )
    task.status = TaskStatus.BIDDING
    task.bidding_deadline = datetime.now(timezone.utc) + timedelta(days=bidding_days)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.publish",
        target_type="task", target_id=str(task_id),
        details=f"Task published to bidding pool, deadline in {bidding_days} days",
        ip_address=None,
    )
    return task


@router.post(
    "/{task_id}/convert-urgent",
    response_model=TaskPublic,
    summary="转换为紧急任务（管理员）",
    description="管理员将任务类型转换为 'urgent'",
)
async def convert_to_urgent(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(TaskScope.CONVERT))],
) -> Any:
    """转换为紧急任务"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    if task.task_type == TaskType.URGENT:
        raise BusinessException(code=ErrorCode.TASK_INVALID_STATUS_TRANSITION, detail="Task is already urgent.")
    task.task_type = TaskType.URGENT
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.convert_type",
        target_type="task", target_id=str(task_id),
        details=f"Task type converted to urgent", ip_address=None,
    )
    return task


@router.post(
    "/{task_id}/convert-convenient",
    response_model=TaskPublic,
    summary="转换为便捷任务（管理员）",
    description="管理员将任务类型转换为 'convenient'",
)
async def convert_to_convenient(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(TaskScope.CONVERT))],
) -> Any:
    """转换为便捷任务"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    if task.task_type == TaskType.CONVENIENT:
        raise BusinessException(code=ErrorCode.TASK_INVALID_STATUS_TRANSITION, detail="Task is already convenient.")
    task.task_type = TaskType.CONVENIENT
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.convert_type",
        target_type="task", target_id=str(task_id),
        details=f"Task type converted to convenient", ip_address=None,
    )
    return task


# ==================== 管理员：暂停审批和改派 ====================


@router.post(
    "/{task_id}/pause-approve",
    response_model=TaskPublic,
    summary="审批暂停（管理员）",
    description="管理员审批确认任务暂停，状态从 PAUSE_REQUESTED 变为 PAUSED",
)
async def pause_approve_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> Any:
    """审批暂停 — 需要管理员权限"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_admin_scope(session, current_user)
    await check_task_status(task, TaskStatus.PAUSE_REQUESTED)
    task.status = TaskStatus.PAUSED
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.pause_approve",
        target_type="task", target_id=str(task_id),
        details=f"Task pause approved by admin", ip_address=None,
    )
    return task


@router.post(
    "/{task_id}/pause-reject",
    response_model=TaskPublic,
    summary="驳回暂停（管理员）",
    description="管理员驳回工程师的暂停申请，状态回到 IN_PROGRESS",
)
async def pause_reject_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> Any:
    """驳回暂停申请 — 需要管理员权限"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_admin_scope(session, current_user)
    await check_task_status(task, TaskStatus.PAUSE_REQUESTED)
    task.status = TaskStatus.IN_PROGRESS
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.pause_reject",
        target_type="task", target_id=str(task_id),
        details=f"Task pause rejected by admin", ip_address=None,
    )
    return task


@router.post(
    "/{task_id}/reassign",
    response_model=TaskPublic,
    summary="改派任务（管理员）",
    description="管理员将任务改派给其他工程师，状态变为待开工",
)
async def reassign_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    request: TaskReassignRequest,
) -> Any:
    """改派任务 — 需要管理员权限"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_admin_scope(session, current_user)
    new_engineer = await session.get(User, request.new_engineer_id)
    if not new_engineer:
        raise BusinessException(code=ErrorCode.USER_NOT_FOUND, detail=f"Engineer not found")
    if new_engineer.role != UserRoleType.ENGINEER:
        raise BusinessException(code=ErrorCode.USER_ROLE_MISMATCH, detail="Target user is not an engineer")
    task.engineer_id = request.new_engineer_id
    task.status = TaskStatus.PENDING_START
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.reassign",
        target_type="task", target_id=str(task_id),
        details=f"Task reassigned to engineer {request.new_engineer_id}", ip_address=None,
    )
    return task


# ==================== 工程师：任务执行 ====================


@router.post(
    "/{task_id}/start",
    response_model=TaskPublic,
    summary="启动任务",
    description="工程师启动待开工的任务，状态从 PENDING_START 变为 IN_PROGRESS",
)
async def start_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> Any:
    """启动任务 — 仅被分配的工程师可操作"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_task_assigned_to_engineer(session, current_user, task)
    await check_task_status(task, TaskStatus.PENDING_START)
    task.status = TaskStatus.IN_PROGRESS
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.start",
        target_type="task", target_id=str(task_id),
        details=f"Task started by engineer", ip_address=None,
    )
    return task


@router.post(
    "/{task_id}/decline",
    response_model=TaskPublic,
    summary="拒绝任务",
    description="工程师拒绝待开工的任务，任务重新进入竞价",
)
async def decline_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> Any:
    """拒绝任务 — 重新进入竞价（下一轮）"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_task_assigned_to_engineer(session, current_user, task)
    await check_task_status(task, TaskStatus.PENDING_START)
    task.status = TaskStatus.BIDDING
    task.engineer_id = None
    task.bidding_deadline = datetime.now(timezone.utc) + timedelta(days=1)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.decline",
        target_type="task", target_id=str(task_id),
        details=f"Task declined by engineer, re-entered bidding", ip_address=None,
    )
    return task


@router.post(
    "/{task_id}/pause-request",
    response_model=TaskPublic,
    summary="申请暂停",
    description="工程师申请暂停正在进行的任务",
)
async def pause_request_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> Any:
    """申请暂停 — 需管理员审批"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_task_assigned_to_engineer(session, current_user, task)
    await check_task_status(task, TaskStatus.IN_PROGRESS)
    task.status = TaskStatus.PAUSE_REQUESTED
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.pause_request",
        target_type="task", target_id=str(task_id),
        details=f"Engineer requested pause", ip_address=None,
    )
    return task


@router.post(
    "/{task_id}/resume",
    response_model=TaskPublic,
    summary="恢复任务",
    description="工程师恢复暂停的任务",
)
async def resume_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> Any:
    """恢复暂停任务"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_task_assigned_to_engineer(session, current_user, task)
    await check_task_status(task, TaskStatus.PAUSED)
    task.status = TaskStatus.IN_PROGRESS
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.resume",
        target_type="task", target_id=str(task_id),
        details=f"Task resumed", ip_address=None,
    )
    return task


@router.post(
    "/{task_id}/complete",
    response_model=TaskPublic,
    summary="完成任务",
    description="工程师标记任务完成，填写实际工时",
)
async def complete_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    request: TaskCompleteRequest,
) -> Any:
    """完成任务 — 触发星点计算"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_task_assigned_to_engineer(session, current_user, task)
    await check_task_status(task, TaskStatus.IN_PROGRESS)
    task.status = TaskStatus.COMPLETED
    task.T_reported = request.T_reported
    session.add(task)
    await session.commit()
    await session.refresh(task)
    try:
        await trigger_starpoint_calculation(session=session, task=task)
    except Exception:
        pass
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.complete",
        target_type="task", target_id=str(task_id),
        details=f"Task completed, T_reported={request.T_reported}", ip_address=None,
    )
    await session.refresh(task)
    return task