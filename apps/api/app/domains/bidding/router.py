"""
竞价结算 API 端点模块

提供手动触发竞价结算的 API 接口。
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, SessionDep
from app.core.errors import BusinessException, ErrorCode, raise_task_not_found
from app.core.schemas import Message
from app.core.models import TaskStatus
from app.domains.task.dependencies import check_task_owner_or_admin
from app.tasks.bidding_tasks import settle_bidding_task_async

router = APIRouter()


@router.post(
    "/tasks/{task_id}/settle-bidding",
    response_model=Message,
    summary="手动触发竞价结算",
    description="管理员手动触发竞价结算任务，计算中标人并更新任务状态"
)
async def manual_settle_bidding(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> Any:
    """
    手动触发竞价结算

    权限：管理员或超管

    业务流程：
    1. 检查任务是否存在
    2. 检查权限（管理员）
    3. 执行结算逻辑
    4. 返回结算结果

    异常：
    - 404：任务不存在
    - 403：权限不足
    - 400：任务状态不符合要求
    """
    from app.domains.task import repository

    # 1. 查询任务
    task = await repository.get_task(session=session, task_id=task_id)
    if not task:
        raise_task_not_found()

    # 2. 检查权限（管理员）
    await check_task_owner_or_admin(session, current_user, task.pm_id)

    # 3. 执行结算
    result = await settle_bidding_task_async(session, str(task_id))

    # 4. 根据结果返回消息
    if result["status"] == "success":
        return Message(
            message=f"Settlement completed. Winner: {result['winner_id']}, Amount: {result['winner_amount']}"
        )
    elif result["status"] == "no_bids":
        return Message(message="No bids received. Task reverted to unconfirmed status.")
    elif result["status"] == "deadline_not_reached":
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail="Bidding deadline has not been reached yet."
        )
    else:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Settlement failed: {result['status']}"
        )
