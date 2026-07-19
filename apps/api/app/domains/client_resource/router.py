"""
客资管理 API 端点模块

提供客资相关的 RESTful API 端点：
- POST /client-resources — PM 录入客资
- GET /client-resources — PM 查看自己客资历史
- GET /client-resources/admin — 管理员查看所有 PM 汇总
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
)
from app.core.scopes import ClientResourceScope, UserScope
from app.core.schemas import Message
from app.core.models import User, UserRoleType
from app.core.errors import BusinessException, ErrorCode, raise_user_not_found

from app.domains.client_resource import repository
from app.domains.client_resource.schemas import (
    ClientResourceCreate,
    ClientResourcePublic,
    ClientResourcesPublic,
    ClientResourceSummary,
)


router = APIRouter()


@router.post(
    "",
    response_model=ClientResourcePublic,
    summary="录入客资",
    description="PM 录入自己的客资数据",
)
async def create_client_resource(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    resource_in: ClientResourceCreate,
    _: Annotated[None, Depends(require_scope(ClientResourceScope.CREATE))] = None,
) -> Any:
    """
    录入客资

    权限：PM（需 client-resource:create 权限）

    自动使用 PM 的 baseline_client_count 作为基准客资数。
    """
    # 获取 PM 的基准客资数
    user = await session.get(User, current_user.id)
    if not user or user.baseline_client_count is None:
        raise BusinessException(
            code=ErrorCode.SYSTEM_VALIDATION_ERROR,
            detail="Baseline client count not set for this PM. Please contact admin.",
        )

    resource = await repository.create_client_resource(
        session=session,
        pm_id=current_user.id,
        actual_count=resource_in.actual_count,
        baseline_count=user.baseline_client_count,
        date=resource_in.date,
    )

    return resource


@router.get(
    "",
    response_model=ClientResourcesPublic,
    summary="查看客资历史",
    description="PM 查看自己的客资录入历史",
)
async def read_my_client_resources(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量，默认20")] = 20,
    _: Annotated[None, Depends(require_scope(ClientResourceScope.READ))] = None,
) -> Any:
    """
    获取自己的客资列表

    权限：PM（需 client-resource:read 权限）
    """
    offset = (page - 1) * page_size

    resources, count = await repository.get_client_resources(
        session=session,
        pm_id=current_user.id,
        skip=offset,
        limit=page_size,
    )

    return ClientResourcesPublic(
        data=[ClientResourcePublic.model_validate(r) for r in resources],
        count=count,
        page=page,
        page_size=page_size,
        total_pages=(count + page_size - 1) // page_size if count > 0 else 0,
    )


@router.get(
    "/admin",
    response_model=list[ClientResourceSummary],
    summary="管理员查看客资汇总",
    description="管理员查看所有 PM 的客资数据汇总",
)
async def read_admin_client_resource_summary(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    """
    管理员查看所有 PM 客资汇总

    权限：管理员（需 user:admin 权限）
    """
    summaries = await repository.get_admin_summary(session=session)

    return [ClientResourceSummary(**s) for s in summaries]


@router.get(
    "/all",
    response_model=ClientResourcesPublic,
    summary="管理员查看所有客资",
    description="管理员查看所有 PM 的客资明细记录",
)
async def read_all_client_resources(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量，默认20")] = 20,
    _: Annotated[None, Depends(require_scope(UserScope.ADMIN))] = None,
) -> Any:
    """
    获取所有客资记录（管理员操作）。

    权限：管理员（需 user:admin 权限）
    """
    offset = (page - 1) * page_size

    resources, count = await repository.get_client_resources(
        session=session,
        skip=offset,
        limit=page_size,
    )

    return ClientResourcesPublic(
        data=[ClientResourcePublic.model_validate(r) for r in resources],
        count=count,
        page=page,
        page_size=page_size,
        total_pages=(count + page_size - 1) // page_size if count > 0 else 0,
    )