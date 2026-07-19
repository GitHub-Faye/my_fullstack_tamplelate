"""
Task 审核与发布相关 API

管理员审核任务、发布任务到竞价池、转换任务类型。
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
from app.core.errors import raise_task_not_found, BusinessException, ErrorCode
from app.core.models import Task, TaskStatus, TaskType
from app.core.models import Bid

from app.domains.task import repository
from app.domains.task.schemas import TaskPublic
from app.domains.task.dependencies import check_task_owner_or_admin
from app.domains.user.repository import create_audit_log

router = APIRouter()


# ==================== 管理员端点：审核与发布 ====================


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
    """
    审核通过任务

    - 需要 task:approve 权限
    - 仅 'unconfirmed' 状态的任务可审核
    - 审核后状态变为 'confirmed_unpublished'
    """
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 检查任务状态
    if task.status != TaskStatus.UNCONFIRMED:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Task status '{task.status.value}' cannot be approved. Only 'unconfirmed' tasks can be approved."
        )

    # 更新状态为 confirmed_unpublished
    task.status = TaskStatus.CONFIRMED_UNPUBLISHED
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # 记录审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="task.approve",
        target_type="task",
        target_id=str(task_id),
        details=f"Task approved, status changed to confirmed_unpublished",
        ip_address=None,
    )

    return task


@router.post(
    "/{task_id}/reject",
    response_model=TaskPublic,
    summary="驳回任务（管理员）",
    description="管理员驳回任务，状态保持为 'unconfirmed'，PM 可重新编辑",
)
async def reject_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(TaskScope.APPROVE))],
) -> Any:
    """
    驳回任务

    - 需要 task:approve 权限
    - 仅 'unconfirmed' 状态的任务可驳回
    - 驳回后状态保持为 'unconfirmed'，PM 可重新编辑
    """
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 检查任务状态
    if task.status != TaskStatus.UNCONFIRMED:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Task status '{task.status.value}' cannot be rejected. Only 'unconfirmed' tasks can be rejected."
        )

    # 驳回操作：添加备注（此处简单返回任务信息，实际可在 PM 端显示驳回状态）
    # 状态保持 'unconfirmed'，PM 可重新编辑

    # 记录审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="task.reject",
        target_type="task",
        target_id=str(task_id),
        details=f"Task rejected by admin",
        ip_address=None,
    )

    return task


@router.post(
    "/{task_id}/publish",
    response_model=TaskPublic,
    summary="发布任务到竞价池（管理员）",
    description="管理员发布任务到竞价池，状态变为 'bidding'，设置竞价截止时间",
)
async def publish_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    bidding_days: int = 3,
    _: Annotated[None, Depends(require_scope(TaskScope.APPROVE))],
) -> Any:
    """
    发布任务到竞价池

    - 需要 task:approve 权限
    - 仅 'confirmed_unpublished' 状态的任务可发布
    - 发布后状态变为 'bidding'
    - 设置竞价截止时间（默认 3 天后）
    """
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 检查任务状态
    if task.status != TaskStatus.CONFIRMED_UNPUBLISHED:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Task status '{task.status.value}' cannot be published. Only 'confirmed_unpublished' tasks can be published."
        )

    # 更新状态为 bidding，设置竞价截止时间
    task.status = TaskStatus.BIDDING
    task.bidding_deadline = datetime.now(timezone.utc) + timedelta(days=bidding_days)
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # 记录审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="task.publish",
        target_type="task",
        target_id=str(task_id),
        details=f"Task published to bidding pool, deadline in {bidding_days} days",
        ip_address=None,
    )

    return task


@router.post(
    "/{task_id}/convert-urgent",
    response_model=TaskPublic,
    summary="转换为紧急任务（管理员）",
    description="管理员将任务类型转换为 'urgent'，优先竞价",
)
async def convert_to_urgent(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(TaskScope.CONVERT))],
) -> Any:
    """
    转换为紧急任务

    - 需要 task:convert 权限
    - 仅管理员可操作
    - 任务类型变为 'urgent'
    """
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 检查当前类型
    if task.task_type == TaskType.URGENT:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail="Task is already an urgent task."
        )

    # 更新任务类型
    task.task_type = TaskType.URGENT
    session.add(task)
    await session.commit()
    await session.refresh(task)

    return task


@router.post(
    "/{task_id}/convert-convenient",
    response_model=TaskPublic,
    summary="转换为便捷任务（管理员）",
    description="管理员将任务类型转换为 'convenient'，不参与竞价，按需执行",
)
async def convert_to_convenient(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(TaskScope.CONVERT))],
) -> Any:
    """
    转换为便捷任务

    - 需要 task:convert 权限
    - 仅管理员可操作
    - 任务类型变为 'convenient'
    - 便捷任务不参与竞价，按需执行
    """
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 检查当前类型
    if task.task_type == TaskType.CONVENIENT:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail="Task is already a convenient task."
        )

    # 更新任务类型
    task.task_type = TaskType.CONVENIENT
    session.add(task)
    await session.commit()
    await session.refresh(task)

    return task