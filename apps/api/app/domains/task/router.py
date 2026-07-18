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

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
    require_any_scope,
    get_user_scopes,
)
from app.core.scopes import TaskScope
from app.core.schemas import Message, PaginationParams
from app.core.errors import raise_task_not_found
from app.core.models import Task, TaskStatus

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
    """
    获取任务列表

    - PM 只能看自己的任务
    - 管理员可看所有任务
    - 工程师可查看竞价中的任务（用于报价）
    - 支持按状态过滤
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

    # PM 只能查看自己的任务
    pm_id = None if is_admin else current_user.id

    # 工程师查看竞价任务列表时，不过滤 pm_id
    from app.core.models import UserRoleType, User
    from sqlalchemy import select
    stmt = select(User).where(User.id == current_user.id)
    result = await session.execute(stmt)
    user_with_role = result.scalar_one_or_none()
    if user_with_role and user_with_role.role == UserRoleType.ENGINEER:
        pm_id = None

    # 计算offset
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
    """
    更新任务

    - PM 只能更新自己的任务
    - 只有 'unconfirmed' 状态的任务可编辑
    """
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 检查权限（所有者或管理员）
    await check_task_owner_or_admin(session, current_user, task.pm_id)

    # 检查状态是否可编辑
    await check_task_status_editable(session, current_user, task)

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
    description="删除任务（仅管理员或超管）",
)
async def delete_task(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    _: Annotated[None, Depends(require_any_scope(TaskScope.DELETE, TaskScope.ADMIN))],
) -> Message:
    """
    删除任务

    - 需要 task:delete 权限
    - 通常仅管理员可操作
    """
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 检查权限（所有者或管理员）
    await check_task_owner_or_admin(session, current_user, task.pm_id)

    await repository.delete_task(session=session, db_task=task)
    return Message(message="Task deleted successfully")