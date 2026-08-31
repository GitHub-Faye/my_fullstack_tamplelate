"""
Role 领域 API 路由模块

提供完整的角色管理 RESTful API 端点：
- 获取角色列表（分页）/ 单个角色
- 创建角色（name + scopes）
- 更新角色（可以同时修改 name 和 scopes）
- 删除角色

权限控制（严格走 scope 而非角色/超管判断）：
- 读取: role:read
- 创建: role:create
- 更新: role:update
- 删除: role:delete

说明：
- 路由前缀 /roles 在下方 api.py include_router 时统一附加。
- 角色管理是"完整 CRUD + scope 修改"的业务示例，
  新增业务域时可以此文件为模板。
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    SessionDep,
    require_scope,
)
from app.core.scopes import RoleScope
from app.core.schemas import Message, PaginationParams
from app.core.errors import (
    raise_bad_request,
    raise_role_not_found,
)

from app.domains.role import repository
from app.domains.role.schemas import (
    RoleCreate,
    RolePublic,
    RolesPublic,
    RoleUpdate,
)

router = APIRouter()


@router.get(
    "/",
    response_model=RolesPublic,
)
async def read_roles(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Query()],
    _: Annotated[None, Depends(require_scope(RoleScope.READ))],
) -> Any:
    """
    获取角色列表（分页）。

    权限：拥有 role:read scope。

    返回：
    - RolesPublic：data（角色列表，含 scopes）、count、page、page_size、total_pages
    """
    roles, count = await repository.get_roles(
        session=session,
        skip=pagination.offset,
        limit=pagination.limit,
    )

    data = [
        await repository.get_role_public(session=session, role=role)
        for role in roles
    ]

    return RolesPublic(
        data=data,
        count=count,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(count + pagination.page_size - 1) // pagination.page_size if count > 0 else 0,
    )


@router.get(
    "/{role_id}",
    response_model=RolePublic,
)
async def read_role(
    session: SessionDep,
    role_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(RoleScope.READ))],
) -> Any:
    """
    获取单个角色详情（含 scopes 列表）。

    权限：拥有 role:read scope。
    """
    role = await repository.get_role(session=session, role_id=role_id)
    if not role:
        raise_role_not_found()

    return await repository.get_role_public(session=session, role=role)


@router.post(
    "/",
    response_model=RolePublic,
)
async def create_role(
    *,
    session: SessionDep,
    role_in: RoleCreate,
    _: Annotated[None, Depends(require_scope(RoleScope.CREATE))],
) -> Any:
    """
    创建新角色。

    权限：拥有 role:create scope。

    参数：
    - role_in：RoleCreate（name 必填，scopes 可选）

    异常：
    - 409：角色名已存在
    - 400：包含未定义的 scope
    """
    # 检查角色名唯一性
    existing = await repository.get_role_by_name(session=session, name=role_in.name)
    if existing:
        raise_bad_request(f"Role with name '{role_in.name}' already exists")

    role = await repository.create_role(session=session, role_in=role_in)

    return await repository.get_role_public(session=session, role=role)


@router.patch(
    "/{role_id}",
    response_model=RolePublic,
)
async def update_role(
    *,
    session: SessionDep,
    role_id: uuid.UUID,
    role_in: RoleUpdate,
    _: Annotated[None, Depends(require_scope(RoleScope.UPDATE))],
) -> Any:
    """
    更新角色（修改名字和/或它的 scope 集合）。

    权限：拥有 role:update scope。

    参数：
    - role_id：目标角色 UUID
    - role_in：RoleUpdate（name、scopes 均可选）

    业务规则：
    - 传入 scopes 时整体替换（先删后插），实现增减权限的效果。
    - 系统预置角色（viewer / editor / admin）不允许修改。

    异常：
    - 404：角色不存在
    - 400：角色名与其他角色冲突 / 包含未定义 scope / 修改预置角色
    """
    # 查询目标角色
    role = await repository.get_role(session=session, role_id=role_id)
    if not role:
        raise_role_not_found()

    # 若修改名称，检查唯一性（允许保持原名称）
    if role_in.name and role_in.name != role.name:
        existing = await repository.get_role_by_name(session=session, name=role_in.name)
        if existing and existing.id != role_id:
            raise_bad_request(f"Role with name '{role_in.name}' already exists")

    # 调用 CRUD 更新（name + scopes 整体替换）
    role = await repository.update_role(
        session=session,
        db_role=role,
        role_in=role_in,
    )

    return await repository.get_role_public(session=session, role=role)


@router.delete("/{role_id}")
async def delete_role(
    session: SessionDep,
    role_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(RoleScope.DELETE))],
) -> Message:
    """
    删除角色。

    权限：拥有 role:delete scope。

    注意：
    - 系统预置角色（viewer / editor / admin）不允许删除。
    - 角色删除后，引用它的用户会自动解除关联（UserRole 外键 CASCADE）。

    异常：
    - 404：角色不存在
    - 400：删除预置角色
    """
    role = await repository.get_role(session=session, role_id=role_id)
    if not role:
        raise_role_not_found()

    await repository.delete_role(session=session, db_role=role)
    return Message(message="Role deleted successfully")