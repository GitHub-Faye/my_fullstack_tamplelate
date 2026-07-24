"""
管理员用户管理 API 路由模块

提供管理员专用的用户管理端点：
- 创建工程师/PM 账号（带工资字段）
- 编辑用户信息
- 启用/禁用账号
- 重置密码
- 查看操作日志
"""

import json
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
)
from app.core.scopes import UserScope
from app.core.schemas import Message
from app.core.errors import (
    BusinessException,
    ErrorCode,
    raise_user_not_found,
    raise_user_already_exists,
)
from app.core.models import UserRoleType

from app.domains.user import repository
from app.domains.user.schemas import (
    UserAdminCreate,
    UserAdminDetail,
    UserAdminUpdate,
    UserToggleActive,
    AdminPasswordReset,
    UsersAdminPublic,
)
from app.domains.audit.repository import create_audit_log
from app.domains.audit.schemas import AuditLogPublic, AuditLogList
from app.domains.audit.repository import get_audit_logs


router = APIRouter()


@router.post(
    "/users",
    response_model=UserAdminDetail,
    summary="创建用户（管理员）",
    description="管理员创建工程师或 PM 账号，支持设置角色和工资字段",
)
async def admin_create_user(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_in: UserAdminCreate,
    request: Request,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    """
    创建用户（管理员操作）。

    权限：管理员（需 user:admin 权限，该 scope 仅 admin 角色具有）
    """
    # 检查邮箱唯一性
    existing = await repository.get_user_by_email(session=session, email=user_in.email)
    if existing:
        raise_user_already_exists("User with this email already exists")

    # 创建用户
    user = await repository.create_user_with_role(session=session, user_create=user_in)

    # 分配角色对应的 scope
    role_mapping = {
        "engineer": "engineer",
        "pm": "pm",
        "admin": "admin",
    }
    role_name = role_mapping.get(user_in.role.value, "engineer")
    await repository.assign_user_role(session=session, user=user, role_name=role_name)

    # 记录审计日志
    details = {
        "email": user_in.email,
        "role": user_in.role.value,
        "full_name": user_in.full_name,
    }
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="user.create",
        target_type="user",
        target_id=str(user.id),
        details=json.dumps(details, default=str),
        ip_address=request.client.host if request.client else None,
    )

    return _to_admin_detail(user)


@router.get(
    "/users",
    response_model=UsersAdminPublic,
    summary="获取用户列表（管理员）",
    description="管理员获取所有用户列表，包含工资字段详情",
)
async def admin_read_users(
    session: SessionDep,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    """
    获取用户列表（管理员操作）。

    权限：管理员（需 user:admin 权限）
    """
    offset = (page - 1) * page_size
    users, count = await repository.get_users(session=session, skip=offset, limit=page_size)

    data = [_to_admin_detail(u) for u in users]
    return UsersAdminPublic(
        data=data,
        count=count,
        page=page,
        page_size=page_size,
        total_pages=(count + page_size - 1) // page_size if count > 0 else 0,
    )


@router.get(
    "/users/{user_id}",
    response_model=UserAdminDetail,
    summary="获取用户详情（管理员）",
    description="管理员获取指定用户的详细信息，包含工资字段",
)
async def admin_read_user(
    session: SessionDep,
    current_user: CurrentUser,
    user_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    """
    获取用户详情（管理员操作）。

    权限：管理员（需 user:admin 权限）
    """
    user = await repository.get_user_detail(session=session, user_id=user_id)
    if not user:
        raise_user_not_found()
    return _to_admin_detail(user)


@router.patch(
    "/users/{user_id}",
    response_model=UserAdminDetail,
    summary="更新用户信息（管理员）",
    description="管理员更新用户信息，包括角色、工资字段等",
)
async def admin_update_user(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_id: uuid.UUID,
    user_in: UserAdminUpdate,
    request: Request,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    """
    更新用户信息（管理员操作）。

    权限：管理员（需 user:admin 权限）
    """
    user = await repository.get_user_detail(session=session, user_id=user_id)
    if not user:
        raise_user_not_found()

    # 若修改邮箱，检查唯一性
    if user_in.email and user_in.email != user.email:
        existing = await repository.get_user_by_email(session=session, email=user_in.email)
        if existing and existing.id != user_id:
            raise_user_already_exists("User with this email already exists")

    # 如果角色变更，重新分配角色
    role_changed = user_in.role is not None and user_in.role != user.role

    # 更新用户
    updated_user = await repository.admin_update_user(
        session=session, db_user=user, user_in=user_in
    )

    # 如果角色变更，重新分配 UserRole 关联
    if role_changed:
        await repository.update_user_role(
            session=session,
            user=updated_user,
            new_role=user_in.role,
        )

    # 记录审计日志
    changed_fields = user_in.model_dump(exclude_unset=True, exclude_none=True)
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="user.update",
        target_type="user",
        target_id=str(user_id),
        details=json.dumps(changed_fields, default=str),
        ip_address=request.client.host if request.client else None,
    )

    return _to_admin_detail(updated_user)


@router.post(
    "/users/{user_id}/toggle-active",
    response_model=UserAdminDetail,
    summary="启用/禁用用户（管理员）",
    description="管理员启用或禁用指定用户账号",
)
async def admin_toggle_user_active(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_id: uuid.UUID,
    body: UserToggleActive,
    request: Request,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    """
    启用/禁用用户账号（管理员操作）。

    权限：管理员（需 user:admin 权限）
    """
    user = await repository.get_user_detail(session=session, user_id=user_id)
    if not user:
        raise_user_not_found()

    # 禁止管理员禁用自己
    if user.id == current_user.id:
        raise BusinessException(
            code=ErrorCode.USER_CANNOT_DELETE_SELF,
            detail="Cannot toggle your own active status"
        )

    updated_user = await repository.toggle_user_active(
        session=session, db_user=user, is_active=body.is_active
    )

    # 记录审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="user.toggle_active",
        target_type="user",
        target_id=str(user_id),
        details=json.dumps({"is_active": body.is_active}),
        ip_address=request.client.host if request.client else None,
    )

    return _to_admin_detail(updated_user)


@router.post(
    "/users/{user_id}/reset-password",
    response_model=Message,
    summary="重置用户密码（管理员）",
    description="管理员重置指定用户的密码",
)
async def admin_reset_password(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_id: uuid.UUID,
    body: AdminPasswordReset,
    request: Request,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    """
    重置用户密码（管理员操作）。

    权限：管理员（需 user:admin 权限）
    """
    user = await repository.get_user_detail(session=session, user_id=user_id)
    if not user:
        raise_user_not_found()

    await repository.admin_reset_password(
        session=session, db_user=user, new_password=body.new_password
    )

    # 记录审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="user.reset_password",
        target_type="user",
        target_id=str(user_id),
        ip_address=request.client.host if request.client else None,
    )

    return Message(message="Password reset successfully")


@router.delete(
    "/users/{user_id}",
    response_model=Message,
    summary="删除用户（管理员）",
    description="管理员删除指定用户账号",
)
async def admin_delete_user(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_id: uuid.UUID,
    request: Request,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    """
    删除用户（管理员操作）。

    权限：管理员（需 user:admin 权限）
    """
    user = await repository.get_user_detail(session=session, user_id=user_id)
    if not user:
        raise_user_not_found()

    # 禁止管理员删除自己
    if user.id == current_user.id:
        raise BusinessException(
            code=ErrorCode.USER_CANNOT_DELETE_SELF,
            detail="Cannot delete your own account"
        )

    # 记录审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="user.delete",
        target_type="user",
        target_id=str(user_id),
        details=json.dumps({"email": user.email, "full_name": user.full_name}),
        ip_address=request.client.host if request.client else None,
    )

    await repository.delete_user(session=session, db_user=user)

    return Message(message="User deleted successfully")


@router.get(
    "/audit-logs",
    response_model=AuditLogList,
    summary="查看操作日志（管理员）",
    description="管理员查看系统操作审计日志",
)
async def admin_read_audit_logs(
    session: SessionDep,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
    target_type: Annotated[str | None, Query(description="按目标类型筛选")] = None,
    user_id: Annotated[uuid.UUID | None, Query(description="按操作人筛选")] = None,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    """
    查看操作日志（管理员操作）。

    权限：管理员（需 user:admin 权限）
    """
    offset = (page - 1) * page_size
    logs, count = await get_audit_logs(
        session=session,
        skip=offset,
        limit=page_size,
        target_type=target_type,
        user_id=user_id,
    )

    data = []
    for log in logs:
        operator_name = None
        if log.operator:
            operator_name = log.operator.full_name or log.operator.email
        data.append(AuditLogPublic(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at,
            operator_name=operator_name,
        ))

    return AuditLogList(
        data=data,
        count=count,
        page=page,
        page_size=page_size,
        total_pages=(count + page_size - 1) // page_size if count > 0 else 0,
    )


# ==================== 辅助函数 ====================

def _to_admin_detail(user) -> UserAdminDetail:
    """将 User 模型转换为 UserAdminDetail DTO"""
    return UserAdminDetail(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        role=user.role,
        created_at=user.created_at,
        S0=user.S0,
        H0=user.H0,
        T_monthly_plan=user.T_monthly_plan,
        current_starpoint=user.current_starpoint or 0,
        S_base=user.S_base,
        S_assess=user.S_assess,
        R_base=user.R_base,
        R_assess=user.R_assess,
        phone=user.phone,
        department=user.department,
        hire_date=user.hire_date,
        employment_status=user.employment_status,
    )
