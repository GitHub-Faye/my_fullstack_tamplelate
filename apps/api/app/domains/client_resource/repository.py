"""
客资管理模块数据访问层（Repository）

负责客资相关的数据库操作：录入、查询、汇总等。
"""

import uuid
from datetime import datetime
from typing import Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import ClientResource, User, UserRoleType
from app.core.db_utils import paginated_query


async def create_client_resource(
    *,
    session: AsyncSession,
    pm_id: uuid.UUID,
    actual_count: int,
    baseline_count: int,
    date: datetime,
) -> ClientResource:
    """
    录入客资

    Args:
        session: 数据库会话
        pm_id: PM 用户 ID
        actual_count: 实际客资数
        baseline_count: 基准客资数
        date: 记录日期

    Returns:
        创建的客资记录
    """
    resource = ClientResource(
        pm_id=pm_id,
        actual_count=actual_count,
        baseline_count=baseline_count,
        date=date,
    )
    session.add(resource)
    await session.commit()
    await session.refresh(resource)
    return resource


async def get_client_resources(
    *,
    session: AsyncSession,
    pm_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[list[ClientResource], int]:
    """
    获取客资列表（分页，可选按 PM 过滤）

    Args:
        session: 数据库会话
        pm_id: PM ID（可选，仅查看指定 PM）
        skip: 跳过记录数
        limit: 返回记录数上限

    Returns:
        (客资列表, 总数) 元组
    """
    conditions = []
    if pm_id is not None:
        conditions.append(ClientResource.pm_id == pm_id)

    return await paginated_query(
        session=session,
        model=ClientResource,
        skip=skip,
        limit=limit,
        conditions=conditions or None,
        order_by=ClientResource.date.desc(),
    )


async def get_admin_summary(
    *,
    session: AsyncSession,
) -> list[dict]:
    """
    管理员查看所有 PM 的客资汇总

    按 PM 分组统计：总记录数、总实际客资数、平均客资数。

    Returns:
        PM 汇总列表
    """
    # 查询所有 PM 用户
    stmt = select(User).where(User.role == UserRoleType.PM)
    result = await session.execute(stmt)
    pms = result.scalars().all()

    summaries = []
    for pm in pms:
        # 统计该 PM 的客资记录
        count_stmt = (
            select(func.count(), func.coalesce(func.sum(ClientResource.actual_count), 0))
            .where(ClientResource.pm_id == pm.id)
        )
        count_result = await session.execute(count_stmt)
        row = count_result.one()
        record_count = row[0]
        total_actual = row[1] or 0

        avg_actual = round(total_actual / record_count, 2) if record_count > 0 else 0.0

        # 计算超额完成率
        performance_rate = None
        if pm.baseline_client_count and record_count > 0:
            total_baseline = pm.baseline_client_count * record_count
            if total_baseline > 0:
                performance_rate = round((total_actual - total_baseline) / total_baseline, 4)

        summaries.append({
            "pm_id": pm.id,
            "pm_name": pm.full_name or pm.email,
            "baseline_count": pm.baseline_client_count,
            "total_actual": total_actual,
            "avg_actual": avg_actual,
            "record_count": record_count,
            "performance_rate": performance_rate,
        })

    return summaries