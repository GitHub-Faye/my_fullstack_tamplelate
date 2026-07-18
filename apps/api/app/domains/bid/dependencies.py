"""
Bid 模块依赖项（Dependencies）

提供竞价报价相关的依赖注入函数。
"""

from datetime import datetime, timezone

from app.core.models import Task, TaskStatus, User, UserRoleType
from app.core.errors import BusinessException, ErrorCode


def check_task_bidding(*, task: Task) -> None:
    """
    检查任务是否在竞价中

    Args:
        task: 任务对象

    Raises:
        BusinessException: 任务不在竞价中
    """
    if task.status != TaskStatus.BIDDING:
        raise BusinessException(
            code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
            detail=f"Task status is '{task.status.value}', not in bidding period."
        )


def check_bidding_deadline(*, task: Task) -> None:
    """
    检查是否在竞价截止时间前

    Args:
        task: 任务对象

    Raises:
        BusinessException: 已过竞价截止时间
    """
    if task.bidding_deadline:
        # 确保 deadline 也是 timezone-aware
        deadline = task.bidding_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > deadline:
            raise BusinessException(
                code=ErrorCode.TASK_INVALID_STATUS_TRANSITION,
                detail=f"Bidding deadline has passed. Deadline: {task.bidding_deadline}"
            )


def check_engineer_role(*, user: User) -> None:
    """
    检查用户是否是工程师角色

    Args:
        user: 用户对象

    Raises:
        BusinessException: 用户不是工程师
    """
    if user.role != UserRoleType.ENGINEER:
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="Only engineers can submit bids."
        )


def check_bid_owner(*, user_id: str, engineer_id: str) -> None:
    """
    检查用户是否是报价所有者

    Args:
        user_id: 当前用户 ID
        engineer_id: 报价工程师 ID

    Raises:
        BusinessException: 用户不是报价所有者
    """
    if str(user_id) != str(engineer_id):
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="You can only modify your own bids."
        )
