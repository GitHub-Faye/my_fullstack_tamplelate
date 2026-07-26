"""
星点 API 端点模块

提供星点查看和管理的 RESTful API 端点：
- 查看自己的星点记录
- 查看星点排行榜
- 管理员手动调整星点
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
    get_user_scopes,
)
from app.core.scopes import StarPointScope
from app.core.schemas import Message
from app.core.errors import BusinessException, ErrorCode
from app.core.models import User, JudgmentType

from app.domains.starpoint import repository
from app.domains.starpoint.schemas import (
    StarPointRecordPublic,
    StarPointRecordsPublic,
    StarPointSummary,
    StarPointLeaderboardEntry,
    StarPointLeaderboard,
    StarPointAdjustRequest,
)


router = APIRouter()


# ==================== 工程师端点：星点查看 ====================


@router.get(
    "/my",
    response_model=StarPointRecordsPublic,
    summary="查看星点记录",
    description="查看星点变化明细记录（管理员可指定 engineer_id 查看特定工程师的记录）"
)
async def read_my_starpoints(
    session: SessionDep,
    current_user: CurrentUser,
    engineer_id: Annotated[uuid.UUID | None, Query(description="工程师ID（管理员可指定，普通用户忽略）")] = None,
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量，默认20，最大100")] = 20,
) -> Any:
    """
    获取星点记录

    权限：工程师或 PM（需 starpoint:read 权限）
    管理员可通过 engineer_id 参数查看指定工程师的记录
    """
    # 检查用户是否有 starpoint:read 权限
    user_scopes = await get_user_scopes(session, current_user)
    if StarPointScope.READ.value not in user_scopes:
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="You don't have permission to view starpoints"
        )

    # 确定目标工程师
    target_engineer_id = current_user.id
    if engineer_id:
        is_admin = StarPointScope.ADMIN.value in user_scopes
        if not is_admin:
            raise BusinessException(
                code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
                detail="Only admins can view other engineers' starpoints"
            )
        target_engineer_id = engineer_id

    offset = (page - 1) * page_size

    records, count = await repository.get_starpoint_records(
        session=session,
        engineer_id=target_engineer_id,
        skip=offset,
        limit=page_size,
    )

    return StarPointRecordsPublic(
        data=records,
        count=count,
        page=page,
        page_size=page_size,
        total_pages=(count + page_size - 1) // page_size if count > 0 else 0,
    )


@router.get(
    "/my/summary",
    response_model=StarPointSummary,
    summary="查看星点汇总",
    description="查看星点汇总信息（总数、排名、K系数，管理员可指定 engineer_id）"
)
async def read_my_starpoint_summary(
    session: SessionDep,
    current_user: CurrentUser,
    engineer_id: Annotated[uuid.UUID | None, Query(description="工程师ID（管理员可指定，普通用户忽略）")] = None,
) -> Any:
    """
    获取星点汇总

    包括星点总数、本月获得、排名、K系数
    管理员可通过 engineer_id 参数查看指定工程师的汇总
    """
    target_engineer_id = current_user.id
    if engineer_id:
        user_scopes = await get_user_scopes(session, current_user)
        is_admin = StarPointScope.ADMIN.value in user_scopes
        if not is_admin:
            raise BusinessException(
                code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
                detail="Only admins can view other engineers' starpoints"
            )
        target_engineer_id = engineer_id

    total_starpoints = await repository.get_total_starpoints(
        session=session,
        engineer_id=target_engineer_id,
    )

    current_month_earned = await repository.get_current_month_earned(
        session=session,
        engineer_id=target_engineer_id,
    )

    rank = await repository.get_engineer_rank(
        session=session,
        engineer_id=target_engineer_id,
    )

    k_coefficient = await repository.calculate_k_coefficient(
        session=session,
        engineer_id=target_engineer_id,
    )

    return StarPointSummary(
        total_starpoints=total_starpoints,
        current_month_earned=current_month_earned,
        rank=rank,
        k_coefficient=k_coefficient,
    )


# ==================== 管理员端点：排行榜和管理 ====================


@router.get(
    "/leaderboard",
    response_model=StarPointLeaderboard,
    summary="星点排行榜",
    description="查看所有工程师的星点排行榜（需 starpoint:admin 权限）"
)
async def read_starpoint_leaderboard(
    session: SessionDep,
    current_user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200, description="返回工程师数量，默认100")] = 100,
) -> Any:
    """
    获取星点排行榜

    权限：管理员（需 starpoint:admin 权限）
    工程师也可以查看（但只有 starpoint:read 权限时可以看到自己的排名）
    """
    leaderboard_data = await repository.get_leaderboard(
        session=session,
        limit=limit,
    )

    entries = []
    for i, entry in enumerate(leaderboard_data):
        k = await repository.calculate_k_coefficient(
            session=session,
            engineer_id=entry["engineer_id"],
        )
        entries.append(StarPointLeaderboardEntry(
            engineer_id=entry["engineer_id"],
            engineer_name=entry.get("engineer_name"),
            total_starpoints=entry["total_starpoints"],
            rank=i + 1,
            k_coefficient=k,
        ))

    return StarPointLeaderboard(
        data=entries,
        count=len(entries),
    )


@router.post(
    "/adjust",
    response_model=StarPointRecordPublic,
    summary="手动调整星点（管理员）",
    description="管理员手动调整工程师的星点"
)
async def adjust_starpoint(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    request: StarPointAdjustRequest,
    _: Annotated[None, Depends(require_scope(StarPointScope.ADMIN))],
) -> Any:
    """
    手动调整星点

    权限：管理员（需 starpoint:admin 权限）

    业务流程：
    1. 检查目标工程师是否存在
    2. 创建 MANUAL 类型的星点记录
    """
    # 1. 检查目标工程师是否存在
    engineer = await session.get(User, request.engineer_id)
    if not engineer:
        raise BusinessException(
            code=ErrorCode.USER_NOT_FOUND,
            detail=f"Engineer with id {request.engineer_id} not found"
        )

    # 2. 创建星点记录
    record = await repository.create_starpoint_record(
        session=session,
        engineer_id=request.engineer_id,
        change_amount=request.change_amount,
        judgment_type=JudgmentType.MANUAL,
        reason=request.reason,
    )

    return record
