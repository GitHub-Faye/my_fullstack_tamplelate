"""
Task 模块路由层 — PM 端点

提供 PM 角色专用的任务管理 RESTful API 端点：
- 创建任务
- 查看任务列表
- 查看任务详情
- 更新任务
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
from app.core.schemas import Message
from app.core.errors import raise_task_not_found
from app.core.models import TaskStatus, UserRoleType

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
    """创建新任务 — 需要 task:create 权限"""
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
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量，默认20，最大100")] = 20,
) -> Any:
    """获取任务列表 — PM 只能看自己的，管理员可看所有"""
    user_scopes = await get_user_scopes(session, current_user)
    is_admin = TaskScope.ADMIN.value in user_scopes

    status_filter = None
    if status:
        try:
            status_filter = TaskStatus(status)
        except ValueError:
            pass

    pm_id = None if is_admin else current_user.id
    if current_user.role == UserRoleType.ENGINEER:
        pm_id = None

    offset = (page - 1) * page_size
    tasks, count = await repository.get_tasks(
        session=session,
        pm_id=pm_id,
        status=status_filter,
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
    """获取任务详情 — PM 只能看自己的"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_task_owner_or_admin(session, current_user, task.pm_id)
    return task


@router.put(
    "/{task_id}",
    response_model=TaskPublic,
    summary="更新任务（PM）",
    description="PM 更新任务信息，仅 'unconfirmed' 状态可编辑",
)
async def update_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    task_in: TaskUpdate,
    _: Annotated[None, Depends(require_any_scope(TaskScope.UPDATE, TaskScope.ADMIN))],
) -> Any:
    """更新任务 — PM 只能更新自己的"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_task_owner_or_admin(session, current_user, task.pm_id)
    await check_task_status_editable(session, current_user, task)
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
    description="删除任务（仅管理员或超管）",
)
async def delete_task(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    _: Annotated[None, Depends(require_any_scope(TaskScope.DELETE, TaskScope.ADMIN))],
) -> Message:
    """删除任务 — 需要 task:delete 权限"""
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()
    await check_task_owner_or_admin(session, current_user, task.pm_id)
    await repository.delete_task(session=session, db_task=task)
    return Message(message="Task deleted successfully")