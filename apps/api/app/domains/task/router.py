"""
Task 模块路由层（统一）

提供任务相关的全部 RESTful API 端点，按功能分区：
- PM 任务 CRUD
- 管理员审核与发布
- 管理员暂停审批与改派
- 工程师任务执行
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
    require_any_scope,
    get_user_scopes,
)
from app.core.scopes import TaskScope
from app.core.schemas import Message
from app.core.errors import BusinessException, ErrorCode, raise_task_not_found
from app.core.models import Task, TaskStatus, TaskType, UserRoleType, User

from app.domains.task import repository
from app.domains.task.schemas import (
    TaskCreate,
    AdminTaskCreate,
    TaskPublic,
    TasksPublic,
    TaskUpdate,
)
from app.domains.task.schemas import (
    TaskCompleteRequest,
    TaskReassignRequest,
)
from app.domains.task.dependencies import (
    TaskOr404,
    TaskOwnerOrAdmin,
    check_task_status,
    check_task_assigned_to_engineer,
    check_admin_scope,
    check_task_owner_or_admin,
)
from app.domains.starpoint.calculation import trigger_starpoint_calculation
from app.domains.audit.repository import create_audit_log

router = APIRouter()


# ==================== PM 任务 CRUD ====================


@router.post(
    "/",
    response_model=TaskPublic,
    summary="创建任务（PM）",
    description="PM 创建新任务，初始状态为 'unconfirmed'，等待管理员审核",
)
async def create_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_in: TaskCreate,
    _: Annotated[None, Depends(require_scope(TaskScope.CREATE))],
) -> Any:
    """
    创建新任务

    - 需要 task:create 权限
    - 任务状态自动设为 unconfirmed
    - pm_id 为当前用户 ID
    """
    task = await repository.create_task(
        session=session,
        task_in=task_in,
        pm_id=current_user.id,
    )
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.create",
        target_type="task", target_id=str(task.id),
        details=f"Task '{task.name}' created", ip_address=None,
    )
    return task


@router.get(
    "/",
    response_model=TasksPublic,
    summary="查看任务列表",
    description="PM 查看自己的任务列表，管理员可查看所有任务",
)
async def read_tasks(
    session: SessionDep,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_any_scope(TaskScope.READ, TaskScope.ADMIN))],
    status: Annotated[str | None, Query(description="按状态过滤")] = None,
    task_type: Annotated[str | None, Query(description="按任务类型过滤")] = None,
    engineer_id: Annotated[str | None, Query(description="按工程师ID过滤")] = None,
    pm_id: Annotated[str | None, Query(description="按发布人(PM)ID过滤")] = None,
    exclude_pm_id: Annotated[bool | None, Query(description="排除当前用户的任务，与 pm_id 配合使用")] = None,
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量，默认20，最大100")] = 20,
) -> Any:
    """
    获取任务列表

    - PM 可查看全部任务，通过 pm_id 过滤控制显示范围
    - 管理员可看所有任务，可按 pm_id / engineer_id / task_type 过滤
    - 工程师可查看竞价中的任务（用于报价）
    - 支持按状态、类型、工程师、PM 过滤
    """
    # 解析状态过滤
    status_filter = None
    if status:
        try:
            status_filter = TaskStatus(status)
        except ValueError:
            pass

    # 解析任务类型过滤
    type_filter = None
    if task_type:
        try:
            type_filter = TaskType(task_type)
        except ValueError:
            pass

    # 解析工程师ID过滤
    engineer_uuid = None
    if engineer_id:
        try:
            engineer_uuid = uuid.UUID(engineer_id)
        except ValueError:
            pass

    # 解析 pm_id 和 exclude_pm_id
    pm_uuid = None
    exclude_pm = False
    if current_user.role == UserRoleType.ENGINEER:
        pm_uuid = None
    else:
        if pm_id:
            try:
                pm_uuid = uuid.UUID(pm_id)
            except ValueError:
                pass
        exclude_pm = exclude_pm_id or False

    # 计算offset
    offset = (page - 1) * page_size

    tasks, count = await repository.get_tasks(
        session=session,
        pm_id=pm_uuid,
        exclude_pm_id=exclude_pm,
        status=status_filter,
        task_type=type_filter,
        engineer_id=engineer_uuid,
        skip=offset,
        limit=page_size,
    )

    return TasksPublic(
        data=tasks,
        count=count,
        page=page,
        page_size=page_size,
        total_pages=(count + page_size - 1) // page_size if count > 0 else 0,
    )


@router.get(
    "/{task_id}",
    response_model=TaskPublic,
    summary="查看任务详情",
    description="查看指定任务的详细信息",
)
async def read_task(
    task: TaskOr404,
    _: Annotated[None, Depends(require_any_scope(TaskScope.READ, TaskScope.ADMIN))],
    _task_owner: TaskOwnerOrAdmin,
) -> Any:
    """
    获取任务详情

    - PM 只能查看自己的任务
    - 管理员可查看所有任务
    """
    return task


@router.put(
    "/{task_id}",
    response_model=TaskPublic,
    summary="更新任务（PM）",
    description="PM 更新任务信息，仅 'unconfirmed' 和 'bidding' 状态可编辑",
)
async def update_task(
    *,
    session: SessionDep,
    task: TaskOwnerOrAdmin,
    task_in: TaskUpdate,
    _: Annotated[None, Depends(require_any_scope(TaskScope.UPDATE, TaskScope.ADMIN))],
) -> Any:
    """
    更新任务

    - PM 只能更新自己的任务
    - 'unconfirmed' 和 'bidding' 状态可编辑（PM 在竞价结束前可修改资料）
    """
    # 检查状态是否可编辑（unconfirmed 或 bidding 状态允许编辑）
    if task.status not in (TaskStatus.UNCONFIRMED, TaskStatus.BIDDING):
        raise BusinessException(
            code=ErrorCode.SYSTEM_VALIDATION_ERROR,
            detail=f"Task status '{task.status.value}' cannot be edited. Only 'unconfirmed' or 'bidding' tasks can be modified."
        )

    # 更新任务
    task = await repository.update_task(
        session=session,
        db_task=task,
        task_in=task_in,
    )
    return task


@router.delete(
    "/{task_id}",
    response_model=Message,
    summary="删除任务",
    description="删除未确认状态的任务（PM 所有者或管理员可操作）",
)
async def delete_task(
    session: SessionDep,
    task: TaskOwnerOrAdmin,
    _: Annotated[None, Depends(require_any_scope(TaskScope.DELETE, TaskScope.ADMIN))],
) -> Message:
    """
    删除任务

    - PM 可删除自己发布的未确认任务
    - 管理员可删除任意未确认任务
    """
    # 仅 'unconfirmed' 状态可删除
    if task.status != TaskStatus.UNCONFIRMED:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Task status '{task.status.value}' cannot be deleted. Only 'unconfirmed' tasks can be deleted."
        )

    await repository.delete_task(session=session, db_task=task)
    return Message(message="Task deleted successfully")


@router.post(
    "/{task_id}/withdraw",
    response_model=TaskPublic,
    summary="撤回任务（PM）",
    description="PM 撤回竞价中的任务，状态从 'bidding' 回到 'unconfirmed'",
)
async def withdraw_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task: TaskOwnerOrAdmin,
    _: Annotated[None, Depends(require_scope(TaskScope.UPDATE))],
) -> Any:
    """
    撤回任务

    - PM 撤回自己的竞价中任务
    - 状态从 'bidding' 回到 'unconfirmed'
    - 清除竞价截止时间
    """
    # 仅 'bidding' 状态可撤回
    if task.status != TaskStatus.BIDDING:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Task status '{task.status.value}' cannot be withdrawn. Only 'bidding' tasks can be withdrawn."
        )

    # 状态回退到未确认，清除竞价截止时间
    task.status = TaskStatus.UNCONFIRMED
    task.bidding_deadline = None
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await repository._fill_user_names(session, task)

    await create_audit_log(
        session=session, user_id=current_user.id, action="task.withdraw",
        target_type="task", target_id=str(task.id),
        details="Task withdrawn from bidding, status back to unconfirmed",
        ip_address=None,
    )
    return task


# ==================== 管理员审核与发布 ====================


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
    bidding_days: int = 1,
    _: Annotated[None, Depends(require_scope(TaskScope.APPROVE))],
) -> Any:
    """发布任务到竞价池 — 仅 "unconfirmed" 状态可发布"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    if task.status != TaskStatus.UNCONFIRMED:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Task status '{task.status.value}' cannot be published."
        )
    task.status = TaskStatus.BIDDING
    task.bidding_deadline = datetime.now(timezone.utc) + timedelta(days=bidding_days)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await repository._fill_user_names(session, task)
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


# ==================== 管理员暂停审批与改派 ====================


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
        details=f"Task pause approved by administrator", ip_address=None,
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
        details=f"Task pause rejected by administrator", ip_address=None,
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


@router.post(
    "/{task_id}/restore",
    response_model=TaskPublic,
    summary="恢复任务（管理员）",
    description="管理员恢复暂停中的任务，状态从 PAUSED 变为 IN_PROGRESS",
)
async def admin_restore_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> Any:
    """恢复暂停任务 — 需要管理员权限"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_admin_scope(session, current_user)
    await check_task_status(task, TaskStatus.PAUSED)
    task.status = TaskStatus.IN_PROGRESS
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await create_audit_log(
        session=session, user_id=current_user.id, action="task.admin_restore",
        target_type="task", target_id=str(task_id),
        details=f"Task restored by administrator", ip_address=None,
    )
    return task


@router.post(
    "/create",
    response_model=TaskPublic,
    summary="创建任务（管理员）",
    description="管理员直接创建紧急/便捷任务，可指定工程师",
)
async def admin_create_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_in: AdminTaskCreate,
) -> Any:
    """管理员直接创建任务"""
    await check_admin_scope(session, current_user)

    # 检查工程师是否存在
    engineer = await session.get(User, task_in.engineer_id)
    if not engineer:
        raise BusinessException(code=ErrorCode.USER_NOT_FOUND, detail="Engineer not found")
    if engineer.role != UserRoleType.ENGINEER:
        raise BusinessException(code=ErrorCode.USER_ROLE_MISMATCH, detail="Target user is not an engineer")

    # 创建任务
    task = await repository.create_task(
        session=session,
        task_in=TaskCreate(
            name=task_in.name,
            description=task_in.description,
            task_type=task_in.task_type,
        ),
        pm_id=current_user.id,
    )

    # 管理员创建的紧急/便捷任务直接指派工程师
    task.engineer_id = task_in.engineer_id
    if task.task_type in (TaskType.URGENT, TaskType.CONVENIENT):
        task.status = TaskStatus.PENDING_START

    session.add(task)
    await session.commit()
    await session.refresh(task)

    await create_audit_log(
        session=session, user_id=current_user.id, action="task.admin_create",
        target_type="task", target_id=str(task.id),
        details=f"Task '{task.name}' created by administrator", ip_address=None,
    )
    return task


# ==================== 工程师任务执行 ====================


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
    description="工程师标记任务完成（T报来自竞价报价，无需重复填写）",
)
async def complete_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    request: TaskCompleteRequest,
) -> Any:
    """完成任务 — 触发星点计算（T报取竞价报价时写入的值）"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_task_assigned_to_engineer(session, current_user, task)
    await check_task_status(task, TaskStatus.IN_PROGRESS)
    task.status = TaskStatus.COMPLETED
    task.T_reported_complete_time = datetime.now(timezone.utc)
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
        details=f"Task completed, T_reported={task.T_reported}", ip_address=None,
    )
    await session.refresh(task)
    return task