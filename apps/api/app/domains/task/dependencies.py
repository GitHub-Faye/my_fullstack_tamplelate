"""
Task 模块权限检查依赖

提供任务相关的权限检查函数。
"""

import uuid

from app.core.dependencies import SessionDep, CurrentUser, get_user_scopes
from app.core.scopes import TaskScope
from app.core.errors import raise_permission_denied
from app.core.models import Task, TaskStatus


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
            code=ErrorCode.VALIDATION_ERROR,
            detail=f"Task status '{task.status.value}' cannot be edited. Only 'unconfirmed' tasks can be modified."
        )

    return True


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