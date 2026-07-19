"""
通用数据库辅助函数

提供跨仓库共享的数据库操作辅助工具。
"""

from typing import Any, Tuple, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

M = TypeVar("M", bound=SQLModel)


async def paginated_query(
    *,
    session: AsyncSession,
    model: type[M],
    skip: int,
    limit: int,
    conditions: list[Any] | None = None,
    order_by: Any | None = None,
) -> Tuple[list[M], int]:
    """
    通用分页查询辅助函数。

    封装 COUNT + SELECT ... OFFSET/LIMIT 模式，消除各仓库中的重复代码。

    Args:
        session: 数据库会话
        model: 模型类
        skip: 跳过记录数
        limit: 返回记录数上限
        conditions: 过滤条件列表（可选）
        order_by: 排序表达式（可选，默认按 created_at 降序）

    Returns:
        (结果列表, 总数) 元组
    """
    from sqlalchemy import and_

    # 计数
    count_stmt = select(func.count()).select_from(model)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    result = await session.execute(count_stmt)
    count = result.scalar_one()

    # 查询
    stmt = select(model)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    if order_by is not None:
        stmt = stmt.order_by(order_by)
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    items = list(result.scalars().all())

    return items, count
