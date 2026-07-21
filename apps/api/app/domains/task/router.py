"""
Task 模块路由层

提供任务相关的 RESTful API 端点：
- 创建任务
- 查看任务列表
- 查看任务详情
- 更新任务
"""

import uuid
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
    TaskPublic,
    TasksPublic,
    TaskUpdate,
)
from app.domains.task.dependencies import (
    check_task_owner_or_admin,
    check_task_status_editable,
    check_pm_role,
)
from app.domains.audit.service import create_audit_log

router = APIRouter()


# ==================== PM 端点：任务管理 ====================

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
    # 检查是否是 PM 角色
    await check_pm_role(session, current_user)

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
    user_scopes = await get_user_scopes(session, current_user)
    is_admin = TaskScope.ADMIN.value in user_scopes

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
    # - PM 可查看全部任务，前端通过 pm_id 控制筛选范围
    # - 管理员可查看全部任务，前端通过 pm_id 控制筛选范围
    # - 工程师查看竞价任务列表，不过滤 pm_id
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
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    _: Annotated[None, Depends(require_any_scope(TaskScope.READ, TaskScope.ADMIN))],
) -> Any:
    """
    获取任务详情

    - PM 只能查看自己的任务
    - 管理员可查看所有任务
    """
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 检查权限（所有者或管理员）
    await check_task_owner_or_admin(session, current_user, task.pm_id)

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
    current_user: CurrentUser,
    task_id: uuid.UUID,
    task_in: TaskUpdate,
    _: Annotated[None, Depends(require_any_scope(TaskScope.UPDATE, TaskScope.ADMIN))],
) -> Any:
    """
    更新任务

    - PM 只能更新自己的任务
    - 'unconfirmed' 和 'bidding' 状态可编辑（PM 在竞价结束前可修改资料）
    """
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 检查权限（所有者或管理员）
    await check_task_owner_or_admin(session, current_user, task.pm_id)

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
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> Message:
    """
    删除任务

    - PM 可删除自己发布的未确认任务
    - 管理员可删除任意未确认任务
    """
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 检查权限（所有者或管理员）
    await check_task_owner_or_admin(session, current_user, task.pm_id)

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
    task_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(TaskScope.UPDATE))],
) -> Any:
    """
    撤回任务

    - PM 撤回自己的竞价中任务
    - 状态从 'bidding' 回到 'unconfirmed'
    - 清除竞价截止时间
    """
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 检查权限（所有者）
    if task.pm_id != current_user.id:
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="Only the task owner can withdraw the task"
        )

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

    await create_audit_log(
        session=session, user_id=current_user.id, action="task.withdraw",
        target_type="task", target_id=str(task_id),
        details=f"Task withdrawn from bidding, status back to unconfirmed",
        ip_address=None,
    )
    return task