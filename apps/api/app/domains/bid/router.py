"""
Bid 模块路由层

提供竞价报价相关的 RESTful API 端点：
- 提交报价
- 修改报价
- 查看报价列表
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
)
from app.core.scopes import BidScope
from app.core.errors import raise_task_not_found, raise_bid_not_found
from app.core.models import Task, User

from app.domains.bid import repository
from app.domains.bid.schemas import BidCreate, BidUpdate, BidPublic, BidsPublic
from app.domains.bid.dependencies import (
    check_task_bidding,
    check_bidding_deadline,
    check_engineer_role,
    check_bid_owner,
)

router = APIRouter()


# ==================== 工程师端点：竞价报价 ====================


@router.post(
    "/tasks/{task_id}/bids",
    response_model=BidPublic,
    summary="提交竞价报价（工程师）",
    description="工程师对竞价中的任务提交报价，金额自动计算（amount = H0 × T_reported）",
)
async def create_bid(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    bid_in: BidCreate,
    _: Annotated[None, Depends(require_scope(BidScope.CREATE))],
) -> Any:
    """
    提交竞价报价

    - 需要 bid:create 权限
    - 仅工程师可提交
    - 任务必须在竞价中状态
    - 必须在竞价截止时间前
    - 报价金额自动计算
    """
    # 检查工程师角色
    check_engineer_role(session=session, user=current_user)

    # 获取工程师的 H0（基准时薪）
    # 重新加载用户以获取 H0 字段
    engineer = await session.get(User, current_user.id)
    if not engineer or not engineer.H0:
        # 如果工程师未设置 H0，使用默认值 100
        H0 = 100.0
    else:
        H0 = engineer.H0

    # 获取任务
    task = await session.get(Task, task_id)
    if not task:
        raise_task_not_found()

    # 检查任务状态
    check_task_bidding(session=session, task=task)

    # 检查竞价截止时间
    check_bidding_deadline(session=session, task=task)

    # 检查是否已报价（每个工程师对同一任务只能报价一次）
    existing_bid = await repository.get_bid_by_engineer_task(
        session=session,
        task_id=task_id,
        engineer_id=current_user.id,
    )
    if existing_bid:
        # 如果已报价，则更新
        bid = await repository.update_bid(
            session=session,
            db_bid=existing_bid,
            T_reported=bid_in.T_reported,
            H0=H0,
        )
    else:
        # 创建新报价
        bid = await repository.create_bid(
            session=session,
            task_id=task_id,
            engineer_id=current_user.id,
            T_reported=bid_in.T_reported,
            H0=H0,
        )

    return bid


@router.put(
    "/tasks/{task_id}/bids/{bid_id}",
    response_model=BidPublic,
    summary="修改竞价报价（工程师）",
    description="工程师修改自己的报价，仅竞价窗口内可修改",
)
async def update_bid(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    bid_id: uuid.UUID,
    bid_in: BidUpdate,
    _: Annotated[None, Depends(require_scope(BidScope.UPDATE))],
) -> Any:
    """
    修改竞价报价

    - 需要 bid:update 权限
    - 仅报价所有者可修改
    - 任务必须在竞价中状态
    - 必须在竞价截止时间前
    """
    # 检查工程师角色
    check_engineer_role(session=session, user=current_user)

    # 获取工程师的 H0（基准时薪）
    engineer = await session.get(User, current_user.id)
    if not engineer or not engineer.H0:
        H0 = 100.0
    else:
        H0 = engineer.H0

    # 获取报价
    bid = await repository.get_bid(session=session, bid_id=bid_id)
    if not bid:
        raise_bid_not_found()

    # 检查报价所有权
    check_bid_owner(session=session, user_id=current_user.id, engineer_id=bid.engineer_id)

    # 获取任务
    task = await session.get(Task, task_id)
    if not task:
        raise_task_not_found()

    # 检查任务状态
    check_task_bidding(session=session, task=task)

    # 检查竞价截止时间
    check_bidding_deadline(session=session, task=task)

    # 更新报价
    bid = await repository.update_bid(
        session=session,
        db_bid=bid,
        T_reported=bid_in.T_reported,
        H0=H0,
    )

    return bid


@router.get(
    "/tasks/{task_id}/bids",
    response_model=BidsPublic,
    summary="查看任务的竞价报价列表",
    description="查看指定任务的所有竞价报价",
)
async def read_bids_by_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(BidScope.READ))],
) -> Any:
    """
    查看任务的竞价报价列表

    - 需要 bid:read 权限
    - 管理员和 PM 可查看所有报价
    - 工程师可查看任务报价列表（但看不到自己的竞争对手具体信息）
    """
    # 获取任务
    task = await session.get(Task, task_id)
    if not task:
        raise_task_not_found()

    # 获取报价列表
    bids = await repository.get_bids_by_task(session=session, task_id=task_id)

    return BidsPublic(
        data=bids,
        count=len(bids),
    )


@router.get(
    "/bids/my",
    response_model=BidsPublic,
    summary="查看我的竞价报价",
    description="工程师查看自己提交的所有竞价报价",
)
async def read_my_bids(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_scope(BidScope.READ))],
) -> Any:
    """
    查看我的竞价报价

    - 需要 bid:read 权限
    - 工程师查看自己的报价历史
    """
    # 获取我的报价列表
    bids = await repository.get_bids_by_engineer(
        session=session,
        engineer_id=current_user.id,
    )

    return BidsPublic(
        data=bids,
        count=len(bids),
    )