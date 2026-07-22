"""
角色管理模块 — API 路由

提供角色 CRUD 端点：
- GET /v1/admin/roles — 角色列表（分页）
- POST /v1/admin/roles — 创建角色
- GET /v1/admin/roles/{role_id} — 角色详情
- PUT /v1/admin/roles/{role_id} — 更新角色
- DELETE /v1/admin/roles/{role_id} — 删除角色
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
    raise_rule_not_found,
)
from app.domains.audit.repository import create_audit_log

from app.domains.role import repository
from app.domains.role.schemas import (
    RoleCreate,
    RolePublic,
    RoleUpdate,
    RolesPublic,
)


router = APIRouter()


def _to_role_public(role) -> RolePublic:
    """将 Role 模型转换为 RolePublic DTO"""
    scopes_list = []
    # 安全地访问 scopes（通过 selectinload 已加载）
    for s in (role.scopes or []):
        scopes_list.append(s.scope)
    return RolePublic(
        id=role.id,
        name=role.name,
        scopes=scopes_list,
        created_at=role.created_at,
    )


@router.get(
    "/roles",
    response_model=RolesPublic,
    summary="获取角色列表",
    description="管理员获取所有角色列表，含 scopes 权限范围",
)
async def admin_read_roles(
    session: SessionDep,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    offset = (page - 1) * page_size
    roles, count = await repository.get_roles(
        session=session, skip=offset, limit=page_size
    )

    data = [_to_role_public(r) for r in roles]
    return RolesPublic(
        data=data,
        count=count,
        page=page,
        page_size=page_size,
        total_pages=(count + page_size - 1) // page_size if count > 0 else 0,
    )


@router.post(
    "/roles",
    response_model=RolePublic,
    summary="创建角色",
    description="管理员创建新角色，指定名称和 scopes 权限范围",
)
async def admin_create_role(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    role_in: RoleCreate,
    request: Request,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    # 检查角色名唯一性
    existing = await repository.get_role_by_name(session=session, name=role_in.name)
    if existing:
        raise BusinessException(
            code=ErrorCode.RULE_NOT_FOUND,
            detail=f"Role with name '{role_in.name}' already exists",
        )

    role = await repository.create_role(
        session=session,
        name=role_in.name,
        scopes=role_in.scopes,
    )

    # 审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="role.create",
        target_type="role",
        target_id=str(role.id),
        details=json.dumps({"name": role_in.name, "scopes": role_in.scopes}),
        ip_address=request.client.host if request.client else None,
    )

    return _to_role_public(role)


@router.get(
    "/roles/{role_id}",
    response_model=RolePublic,
    summary="获取角色详情",
    description="管理员获取指定角色的详细信息，含 scopes 权限范围",
)
async def admin_read_role(
    session: SessionDep,
    current_user: CurrentUser,
    role_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    role = await repository.get_role(session=session, role_id=role_id)
    if not role:
        raise_rule_not_found()
    return _to_role_public(role)


@router.put(
    "/roles/{role_id}",
    response_model=RolePublic,
    summary="更新角色",
    description="管理员更新角色名称和/或 scopes 权限范围",
)
async def admin_update_role(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    role_id: uuid.UUID,
    role_in: RoleUpdate,
    request: Request,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    role = await repository.get_role(session=session, role_id=role_id)
    if not role:
        raise_rule_not_found()

    # 如果修改名称，检查唯一性
    if role_in.name and role_in.name != role.name:
        existing = await repository.get_role_by_name(session=session, name=role_in.name)
        if existing and existing.id != role_id:
            raise BusinessException(
                code=ErrorCode.RULE_NOT_FOUND,
                detail=f"Role with name '{role_in.name}' already exists",
            )

    updated_role = await repository.update_role(
        session=session,
        role=role,
        name=role_in.name,
        scopes=role_in.scopes,
    )

    # 审计日志
    changed = {}
    if role_in.name:
        changed["name"] = role_in.name
    if role_in.scopes is not None:
        changed["scopes"] = role_in.scopes
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="role.update",
        target_type="role",
        target_id=str(role_id),
        details=json.dumps(changed, default=str),
        ip_address=request.client.host if request.client else None,
    )

    return _to_role_public(updated_role)


@router.delete(
    "/roles/{role_id}",
    response_model=Message,
    summary="删除角色",
    description="管理员删除指定角色",
)
async def admin_delete_role(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    role_id: uuid.UUID,
    request: Request,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    role = await repository.get_role(session=session, role_id=role_id)
    if not role:
        raise_rule_not_found()

    # 审计日志
    await create_audit_log(
        session=session,
        user_id=current_user.id,
        action="role.delete",
        target_type="role",
        target_id=str(role_id),
        details=json.dumps({"name": role.name}),
        ip_address=request.client.host if request.client else None,
    )

    await repository.delete_role(session=session, role=role)

    return Message(message="Role deleted successfully")