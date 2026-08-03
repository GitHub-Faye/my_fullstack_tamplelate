"""
竞价模块 — 路由层

提供竞价报价、结算和手动触发的完整端点。
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
from app.core.errors import raise_task_not_found, raise_bid_not_found, BusinessException, ErrorCode
from app.core.models import Task
from app.core.utils import get_engineer_H0

from app.domains.bidding import repository
from app.domains.bidding.schemas import BidCreate, BidUpdate, BidPublic, BidsPublic
from app.domains.bidding.dependencies import (
    check_task_bidding,
    check_bidding_deadline,
    check_engineer_role,
    check_bid_owner,
)
from app.domains.task.dependencies import check_task_owner_or_admin

router = APIRouter()


# ========== 工程师：报价 ==========


@router.post(
    "/tasks/{task_id}/bids",
    response_model=BidPublic,
    summary="提交竞价报价（工程师）",
    description="工程师对竞价中的任务提交报价",
)
async def create_bid(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    bid_in: BidCreate,
    _: Annotated[None, Depends(require_scope(BidScope.CREATE))],
) -> Any:
    check_engineer_role(user=current_user)
    H0 = await get_engineer_H0(session, current_user.id)
    task = await session.get(Task, task_id)
    if not task:
        raise_task_not_found()
    check_task_bidding(task=task)
    check_bidding_deadline(task=task)

    existing_bid = await repository.get_bid_by_engineer_task(
        session=session, task_id=task_id, engineer_id=current_user.id,
    )
    if existing_bid:
        bid = await repository.update_bid(
            session=session, db_bid=existing_bid, T_reported=bid_in.T_reported, H0=H0,
        )
    else:
        bid = await repository.create_bid(
            session=session, task_id=task_id, engineer_id=current_user.id, T_reported=bid_in.T_reported, H0=H0,
        )
    return bid


@router.put(
    "/tasks/{task_id}/bids/{bid_id}",
    response_model=BidPublic,
    summary="修改竞价报价（工程师）",
    description="工程师修改自己的报价",
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
    check_engineer_role(user=current_user)
    H0 = await get_engineer_H0(session, current_user.id)
    bid = await repository.get_bid(session=session, bid_id=bid_id)
    if not bid:
        raise_bid_not_found()
    check_bid_owner(user_id=current_user.id, engineer_id=bid.engineer_id)
    task = await session.get(Task, task_id)
    if not task:
        raise_task_not_found()
    check_task_bidding(task=task)
    check_bidding_deadline(task=task)
    bid = await repository.update_bid(
        session=session, db_bid=bid, T_reported=bid_in.T_reported, H0=H0,
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
    task = await session.get(Task, task_id)
    if not task:
        raise_task_not_found()
    bids = await repository.get_bids_by_task(session=session, task_id=task_id)
    bid_publics = [BidPublic.model_validate(b) for b in bids]
    await repository._fill_engineer_names(session, bid_publics)
    return BidsPublic(data=bid_publics, count=len(bid_publics))


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
    bids = await repository.get_bids_by_engineer(session=session, engineer_id=current_user.id)
    bid_publics = [BidPublic.model_validate(b) for b in bids]
    await repository._fill_engineer_names(session, bid_publics)
    return BidsPublic(data=bid_publics, count=len(bid_publics))


# ========== 管理员：结算 ==========


@router.post(
    "/tasks/{task_id}/settle-bidding",
    response_model=Any,
    summary="手动触发竞价结算",
    description="管理员手动触发竞价结算",
)
async def manual_settle_bidding(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> Any:
    from app.core.schemas import Message

    task = await session.get(Task, task_id)
    if not task:
        raise_task_not_found()
    await check_task_owner_or_admin(session, current_user, task.pm_id)

    result = await repository.settle_bidding_task_async(session, str(task_id), force=True)

    if result["status"] == "success":
        return Message(message=f"Settlement completed. Winner: {result['winner_id']}")
    elif result["status"] == "no_bids":
        return Message(message="No bids received. Task reverted.")
    elif result["status"] == "deadline_not_reached":
        raise BusinessException(code=ErrorCode.TASK_INVALID_STATUS_TRANSITION, detail="Deadline not reached.")
    else:
        raise BusinessException(code=ErrorCode.TASK_INVALID_STATUS_TRANSITION, detail=f"Settlement failed: {result['status']}")