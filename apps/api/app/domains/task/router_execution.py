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
from datetime import datetime, timezone, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, SessionDep
from app.core.errors import BusinessException, ErrorCode, raise_task_not_found
from app.core.schemas import Message
from app.core.models import Task, TaskStatus, UserRoleType, User

from app.domains.task import repository
from app.domains.task.schemas import TaskPublic
from app.domains.task.schemas_execution import (
    TaskCompleteRequest,
)
from app.domains.task.dependencies import (
    check_task_status,
    check_task_assigned_to_engineer,
)
from app.domains.starpoint.calculation import trigger_starpoint_calculation
from app.domains.audit.service import create_audit_log


router = APIRouter()


# ==================== 工程师端点：任务执行 ====================



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

    # 记录审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="task.start",
        target_type="task",
        target_id=str(task_id),
        details=f"Task started by engineer",
        ip_address=None,
    )

    return task


@router.post(
    "/{task_id}/decline",
    response_model=TaskPublic,
    summary="拒绝任务",
    description="工程师拒绝待开工的任务，任务重新进入竞价（设置新的竞价截止时间）"
)
async def decline_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> Any:
    """
    拒绝任务

    权限：被分配的工程师

    Spec §23：全部拒绝时进入下一轮竞价。
    业务流程：
    1. 检查任务是否存在
    2. 检查权限（被分配的工程师）
    3. 检查状态（必须是 PENDING_START）
    4. 清空 engineer_id，重新进入竞价（bidding 状态），设置新的竞价截止时间
    """
    # 1. 查询任务
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 2. 检查权限（被分配的工程师）
    await check_task_assigned_to_engineer(session, current_user, task)

    # 3. 检查状态
    await check_task_status(task, TaskStatus.PENDING_START)

    # 4. 更新状态：重新进入竞价（进入下一轮）
    task.status = TaskStatus.BIDDING
    task.engineer_id = None
    task.bidding_deadline = datetime.now(timezone.utc) + timedelta(days=1)
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # 记录审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="task.decline",
        target_type="task",
        target_id=str(task_id),
        details=f"Task declined by engineer, re-entered bidding with new deadline",
        ip_address=None,
    )

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
) -> Any:
    """
    申请暂停任务

    权限：被分配的工程师

    业务流程：
    1. 检查任务是否存在
    2. 检查权限（被分配的工程师）
    3. 检查状态（必须是 IN_PROGRESS）
    4. 更新状态为 PAUSE_REQUESTED（待管理员审批）
    """
    # 1. 查询任务
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 2. 检查权限（被分配的工程师）
    await check_task_assigned_to_engineer(session, current_user, task)

    # 3. 检查状态
    await check_task_status(task, TaskStatus.IN_PROGRESS)

    # 4. 更新状态为 PAUSE_REQUESTED（等待管理员审批）
    task.status = TaskStatus.PAUSE_REQUESTED
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # 记录审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="task.pause_request",
        target_type="task",
        target_id=str(task_id),
        details=f"Engineer requested pause",
        ip_address=None,
    )

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

    # 记录审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="task.resume",
        target_type="task",
        target_id=str(task_id),
        details=f"Task resumed",
        ip_address=None,
    )

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

    # 5. 触发星点计算
    try:
        await trigger_starpoint_calculation(
            session=session,
            task=task,
        )
    except Exception:
        # 星点计算失败不应影响任务完成操作
        pass

    # 记录审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="task.complete",
        target_type="task",
        target_id=str(task_id),
        details=f"Task completed, T_reported={request.T_reported}",
        ip_address=None,
    )

    await session.refresh(task)
    return task