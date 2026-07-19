"""
日报 API 端点模块

提供日报填报和查询相关的 RESTful API 端点：
- 填写日报
- 查看日报列表
- 查看日报详情
- 更新日报
"""

import uuid
from datetime import date, datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
    require_any_scope,
    get_user_scopes,
)
from app.core.scopes import ReportScope
from app.core.schemas import Message
from app.core.errors import BusinessException, ErrorCode
from app.core.models import User, UserRoleType, Task, TaskStatus, ReportStage

from app.domains.daily_report import repository
from app.domains.daily_report.schemas import (
    DailyReportCreate,
    DailyReportPublic,
    DailyReportsPublic,
    DailyReportUpdate,
    RemindResult,
)


router = APIRouter()


# ==================== 工程师端点：日报填报 ====================


async def check_engineer_role(session: SessionDep, current_user: CurrentUser) -> None:
    """
    检查当前用户是否是工程师角色

    Args:
        session: 数据库会话
        current_user: 当前用户

    Raises:
        BusinessException: 403 用户不是工程师
    """
    from sqlalchemy import select
    stmt = select(User).where(User.id == current_user.id)
    result = await session.execute(stmt)
    user_with_role = result.scalar_one_or_none()

    if not user_with_role or user_with_role.role != UserRoleType.ENGINEER:
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="Only engineers can submit daily reports"
        )


async def check_report_owner_or_admin(
    session: SessionDep,
    current_user: CurrentUser,
    report_engineer_id: uuid.UUID,
) -> None:
    """
    检查是否是日报所有者或管理员

    Args:
        session: 数据库会话
        current_user: 当前用户
        report_engineer_id: 日报所属工程师 ID

    Raises:
        BusinessException: 403 权限不足
    """
    user_scopes = await get_user_scopes(session, current_user)
    is_admin = ReportScope.ADMIN.value in user_scopes

    if not is_admin and current_user.id != report_engineer_id:
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="You can only access your own reports"
        )


@router.post(
    "/",
    response_model=DailyReportPublic,
    summary="填写日报",
    description="工程师填写日报，记录今日工作时长、进度、阶段等信息"
)
async def create_daily_report(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    report_in: DailyReportCreate,
) -> Any:
    """
    填写日报

    权限：工程师

    业务流程：
    1. 检查用户是否是工程师
    2. 检查任务是否存在
    3. 检查是否已有当日该任务的日报
    4. 创建日报
    5. 累加任务的 T_actual（根据今日投入工时）
    6. 同步任务状态（根据日报的 current_stage）
    """
    # 1. 检查用户是否是工程师
    await check_engineer_role(session, current_user)

    # 2. 检查任务是否存在
    from app.core.models import Task
    task = await session.get(Task, report_in.task_id)
    if not task:
        raise BusinessException(
            code=ErrorCode.TASK_NOT_FOUND,
            detail="Task not found"
        )

    # 检查任务是否分配给当前工程师
    if task.engineer_id != current_user.id:
        raise BusinessException(
            code=ErrorCode.TASK_NOT_ASSIGNED_TO_USER,
            detail="Task is not assigned to you"
        )

    # 3. 检查是否已有当日该任务的日报
    report_date = report_in.report_date or date.today()
    exists = await repository.check_report_exists_for_date(
        session=session,
        engineer_id=current_user.id,
        task_id=report_in.task_id,
        report_date=report_date,
    )
    if exists:
        raise BusinessException(
            code=ErrorCode.REPORT_ALREADY_SUBMITTED,
            detail=f"Daily report already submitted for task {report_in.task_id} on {report_date}"
        )

    # 4. 创建日报
    report = await repository.create_daily_report(
        session=session,
        report_in=report_in,
        engineer_id=current_user.id,
    )

    # 5. 累加任务的 T_actual（根据今日投入工时）
    if task.T_actual is None:
        task.T_actual = 0.0
    task.T_actual += report_in.today_hours

    # 6. 同步任务状态（根据日报的 current_stage）
    # 如果日报标记为 completed，则同步任务状态为 COMPLETED
    if report_in.current_stage == ReportStage.COMPLETED and task.status == TaskStatus.IN_PROGRESS:
        task.status = TaskStatus.COMPLETED
        # Spec §27: 阶段选择"已完成"时，进度自动设为 100%
        if not report_in.progress:
            report_in.progress = "100%"
    # 如果日报标记为 paused，则同步任务状态为 PAUSED
    elif report_in.current_stage == ReportStage.PAUSED and task.status == TaskStatus.IN_PROGRESS:
        task.status = TaskStatus.PAUSED

    # 同步进度描述到任务（使用专用 progress 字段，不污染 PM 原始描述）
    # Spec §27: 阶段选择"已完成"时，进度自动设为 100%
    if report_in.current_stage == ReportStage.COMPLETED:
        task.progress = "100%"
    elif report_in.progress:
        task.progress = report_in.progress

    session.add(task)
    await session.commit()

    await session.refresh(report)
    return report


@router.get(
    "/",
    response_model=DailyReportsPublic,
    summary="查看日报列表",
    description="工程师查看自己的日报列表，PM/管理员查看所有日报"
)
async def read_daily_reports(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: Annotated[uuid.UUID | None, Query(description="按任务过滤")] = None,
    report_date: Annotated[date | None, Query(description="按日期过滤")] = None,
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量，默认20，最大100")] = 20,
) -> Any:
    """
    获取日报列表

    - 工程师只能看自己的日报
    - PM/管理员可看所有日报
    - 支持按任务、日期过滤
    """
    user_scopes = await get_user_scopes(session, current_user)
    is_admin = ReportScope.ADMIN.value in user_scopes

    # 工程师只能查看自己的日报
    # PM 可查看所有日报（用于跟踪任务进度）
    # 管理员可查看所有日报
    engineer_id = None if (is_admin or current_user.role == UserRoleType.PM) else current_user.id

    # 计算offset
    offset = (page - 1) * page_size

    reports, count = await repository.get_daily_reports(
        session=session,
        engineer_id=engineer_id,
        task_id=task_id,
        report_date=report_date,
        skip=offset,
        limit=page_size,
    )

    return DailyReportsPublic(
        data=reports,
        count=count,
        page=page,
        page_size=page_size,
        total_pages=(count + page_size - 1) // page_size if count > 0 else 0,
    )


@router.get(
    "/remind",
    response_model=RemindResult,
    summary="查看未提交日报的工程师（管理员）",
    description="管理员查看今日未提交日报的工程师列表，用于提醒"
)
async def get_remind_report(
    session: SessionDep,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_scope(ReportScope.ADMIN))] = None,
) -> Any:
    """
    获取未提交日报的工程师列表

    权限：管理员（需 report:admin 权限）
    """
    today = date.today()

    not_submitted = await repository.get_engineers_not_submitted_today(
        session=session,
        report_date=today,
    )

    # 查询所有工程师总数
    stmt = select(User).where(User.role == UserRoleType.ENGINEER)
    result = await session.execute(stmt)
    all_engineers = result.scalars().all()
    total_engineers = len(all_engineers)
    submitted_today = total_engineers - len(not_submitted)

    return RemindResult(
        total_engineers=total_engineers,
        submitted_today=submitted_today,
        not_submitted=len(not_submitted),
        not_submitted_engineers=[e.full_name or e.email for e in not_submitted],
    )


@router.get(
    "/{report_id}",
    response_model=DailyReportPublic,
    summary="查看日报详情",
    description="查看指定日报的详细信息"
)
async def read_daily_report(
    session: SessionDep,
    current_user: CurrentUser,
    report_id: uuid.UUID,
) -> Any:
    """
    获取日报详情

    - 工程师只能查看自己的日报
    - PM/管理员可查看所有日报
    """
    report = await repository.get_daily_report(session=session, report_id=report_id)
    if not report:
        raise BusinessException(
            code=ErrorCode.REPORT_NOT_FOUND,
            detail="Daily report not found"
        )

    # 检查权限（所有者或管理员）
    await check_report_owner_or_admin(session, current_user, report.engineer_id)

    return report


@router.put(
    "/{report_id}",
    response_model=DailyReportPublic,
    summary="更新日报",
    description="工程师更新自己的日报"
)
async def update_daily_report(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    report_id: uuid.UUID,
    report_in: DailyReportUpdate,
) -> Any:
    """
    更新日报

    - 工程师只能更新自己的日报
    - 仅当天的日报可更新
    """
    report = await repository.get_daily_report(session=session, report_id=report_id)
    if not report:
        raise BusinessException(
            code=ErrorCode.REPORT_NOT_FOUND,
            detail="Daily report not found"
        )

    # 检查权限（所有者）
    if current_user.id != report.engineer_id:
        raise BusinessException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            detail="You can only update your own reports"
        )

    # 检查是否是当天的日报（可选规则，根据业务需求调整）
    # if report.report_date.date() != date.today():
    #     raise BusinessException(
    #         code=ErrorCode.REPORT_CANNOT_MODIFY,
    #         detail="Can only modify today's report"
    #     )

    # 更新日报
    report = await repository.update_daily_report(
        session=session,
        db_report=report,
        report_in=report_in,
    )

    return report


@router.delete(
    "/{report_id}",
    response_model=Message,
    summary="删除日报",
    description="删除日报（仅管理员或超管）"
)
async def delete_daily_report(
    session: SessionDep,
    current_user: CurrentUser,
    report_id: uuid.UUID,
    _: Annotated[None, Depends(require_any_scope(ReportScope.ADMIN))],
) -> Message:
    """
    删除日报

    - 需要 report:admin 权限
    - 通常仅管理员可操作
    """
    report = await repository.get_daily_report(session=session, report_id=report_id)
    if not report:
        raise BusinessException(
            code=ErrorCode.REPORT_NOT_FOUND,
            detail="Daily report not found"
        )

    # 检查权限（所有者或管理员）
    await check_report_owner_or_admin(session, current_user, report.engineer_id)

    await repository.delete_daily_report(session=session, db_report=report)
    return Message(message="Daily report deleted successfully")