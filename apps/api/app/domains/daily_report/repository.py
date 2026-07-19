"""
日报模块数据访问层（Repository）

负责日报相关的数据库操作：CRUD、查询、统计等。
"""

import uuid
from datetime import date, datetime
from typing import Optional, Tuple

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import DailyReport, User, UserRoleType, Task
from app.domains.daily_report.schemas import DailyReportCreate, DailyReportUpdate


async def get_engineers_not_submitted_today(
    *,
    session: AsyncSession,
    report_date: date,
) -> list[User]:
    """
    获取今日未提交日报的工程师列表

    Args:
        session: 数据库会话
        report_date: 报告日期

    Returns:
        未提交日报的工程师列表
    """
    start_datetime = datetime.combine(report_date, datetime.min.time())
    end_datetime = datetime.combine(report_date, datetime.max.time())

    # 查询所有工程师
    engineer_stmt = select(User).where(User.role == UserRoleType.ENGINEER)
    engineer_result = await session.execute(engineer_stmt)
    all_engineers = engineer_result.scalars().all()

    # 查询今日已提交日报的工程师 ID
    submitted_stmt = (
        select(DailyReport.engineer_id)
        .where(
            and_(
                DailyReport.report_date >= start_datetime,
                DailyReport.report_date <= end_datetime,
            )
        )
        .distinct()
    )
    submitted_result = await session.execute(submitted_stmt)
    submitted_ids = {row[0] for row in submitted_result}

    # 筛选未提交的工程师
    not_submitted = [e for e in all_engineers if e.id not in submitted_ids]
    return not_submitted


# ============================== DailyReport CRUD Operations ==============================

async def get_daily_report(*, session: AsyncSession, report_id: uuid.UUID) -> DailyReport | None:
    """
    根据 ID 获取日报

    Args:
        session: 数据库会话
        report_id: 日报 UUID

    Returns:
        DailyReport 对象或 None
    """
    return await session.get(DailyReport, report_id)


async def get_daily_reports(
    *,
    session: AsyncSession,
    engineer_id: Optional[uuid.UUID] = None,
    task_id: Optional[uuid.UUID] = None,
    report_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[list[DailyReport], int]:
    """
    获取日报列表（分页），支持按工程师、任务、日期过滤

    Args:
        session: 数据库会话
        engineer_id: 工程师 ID 过滤（None 表示不过滤）
        task_id: 任务 ID 过滤（None 表示不过滤）
        report_date: 报告日期过滤（None 表示不过滤）
        skip: 跳过记录数
        limit: 返回记录数上限

    Returns:
        (日报列表, 总数) 元组
    """
    # 构建计数查询
    count_statement = select(func.count()).select_from(DailyReport)
    if engineer_id:
        count_statement = count_statement.where(DailyReport.engineer_id == engineer_id)
    if task_id:
        count_statement = count_statement.where(DailyReport.task_id == task_id)
    if report_date:
        count_statement = count_statement.where(DailyReport.report_date >= datetime.combine(report_date, datetime.min.time()))
        count_statement = count_statement.where(DailyReport.report_date < datetime.combine(report_date, datetime.max.time()))

    result = await session.execute(count_statement)
    count = result.scalar_one()

    # 构建查询
    statement = select(DailyReport).order_by(DailyReport.created_at.desc())
    if engineer_id:
        statement = statement.where(DailyReport.engineer_id == engineer_id)
    if task_id:
        statement = statement.where(DailyReport.task_id == task_id)
    if report_date:
        statement = statement.where(DailyReport.report_date >= datetime.combine(report_date, datetime.min.time()))
        statement = statement.where(DailyReport.report_date < datetime.combine(report_date, datetime.max.time()))

    statement = statement.offset(skip).limit(limit)
    result = await session.execute(statement)
    reports = result.scalars().all()

    return list(reports), count


async def create_daily_report(
    *,
    session: AsyncSession,
    report_in: DailyReportCreate,
    engineer_id: uuid.UUID,
) -> DailyReport:
    """
    创建新日报

    Args:
        session: 数据库会话
        report_in: 日报创建数据
        engineer_id: 工程师用户 ID

    Returns:
        创建的日报对象
    """
    # 处理报告日期
    report_date = report_in.report_date or date.today()
    report_datetime = datetime.combine(report_date, datetime.min.time())

    db_report = DailyReport(
        **report_in.model_dump(exclude={"report_date"}),
        engineer_id=engineer_id,
        report_date=report_datetime,
    )
    session.add(db_report)
    await session.commit()
    await session.refresh(db_report)
    return db_report


async def update_daily_report(
    *,
    session: AsyncSession,
    db_report: DailyReport,
    report_in: DailyReportUpdate,
) -> DailyReport:
    """
    更新日报

    Args:
        session: 数据库会话
        db_report: 现有日报对象
        report_in: 日报更新数据

    Returns:
        更新后的日报对象
    """
    update_data = report_in.model_dump(exclude_unset=True)
    db_report.sqlmodel_update(update_data)
    session.add(db_report)
    await session.commit()
    await session.refresh(db_report)
    return db_report


async def delete_daily_report(*, session: AsyncSession, db_report: DailyReport) -> None:
    """
    删除日报

    Args:
        session: 数据库会话
        db_report: 要删除的日报对象
    """
    await session.delete(db_report)
    await session.commit()


async def count_daily_reports_by_engineer(*, session: AsyncSession, engineer_id: uuid.UUID) -> int:
    """
    统计工程师的日报数量

    Args:
        session: 数据库会话
        engineer_id: 工程师用户 ID

    Returns:
        日报数量
    """
    statement = select(func.count()).select_from(DailyReport).where(DailyReport.engineer_id == engineer_id)
    result = await session.execute(statement)
    return result.scalar_one()


async def check_report_exists_for_date(
    *,
    session: AsyncSession,
    engineer_id: uuid.UUID,
    task_id: uuid.UUID,
    report_date: date,
) -> bool:
    """
    检查指定日期是否已有日报

    Args:
        session: 数据库会话
        engineer_id: 工程师用户 ID
        task_id: 任务 ID
        report_date: 报告日期

    Returns:
        是否存在日报
    """
    start_datetime = datetime.combine(report_date, datetime.min.time())
    end_datetime = datetime.combine(report_date, datetime.max.time())

    statement = select(func.count()).select_from(DailyReport).where(
        and_(
            DailyReport.engineer_id == engineer_id,
            DailyReport.task_id == task_id,
            DailyReport.report_date >= start_datetime,
            DailyReport.report_date <= end_datetime,
        )
    )
    result = await session.execute(statement)
    count = result.scalar_one()
    return count > 0