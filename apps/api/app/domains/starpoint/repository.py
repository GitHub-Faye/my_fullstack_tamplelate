"""
星点模块数据访问层（Repository）

负责星点相关的数据库操作：CRUD、查询、统计等。
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import StarPointRecord, User, JudgmentType, RuleCategory
from app.core.db_utils import paginated_query
from app.domains.system_rule import repository as rule_repo

# ====================== 默认 K 系数配置 ======================
_DEFAULT_K_CONFIG = {
    "top_k": 1.2,
    "middle_k": 1.0,
    "bottom_k": 0.7,
    "top_ratio": 0.2,
    "bottom_ratio": 0.2,
}


# ============================== StarPointRecord CRUD ==============================

async def get_starpoint_record(
    *,
    session: AsyncSession,
    record_id: uuid.UUID,
) -> StarPointRecord | None:
    """根据 ID 获取星点记录"""
    return await session.get(StarPointRecord, record_id)


async def get_starpoint_records(
    *,
    session: AsyncSession,
    engineer_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[list[StarPointRecord], int]:
    """
    获取工程师的星点记录（分页）

    Args:
        session: 数据库会话
        engineer_id: 工程师 ID
        skip: 跳过记录数
        limit: 返回记录数上限

    Returns:
        (星点记录列表, 总数) 元组
    """
    return await paginated_query(
        session=session,
        model=StarPointRecord,
        skip=skip,
        limit=limit,
        conditions=[StarPointRecord.engineer_id == engineer_id],
        order_by=StarPointRecord.created_at.desc(),
    )


async def create_starpoint_record(
    *,
    session: AsyncSession,
    engineer_id: uuid.UUID,
    change_amount: int,
    judgment_type: JudgmentType,
    task_id: Optional[uuid.UUID] = None,
    reason: Optional[str] = None,
    T_reported: Optional[float] = None,
    T_actual: Optional[float] = None,
) -> StarPointRecord:
    """
    创建星点记录

    同时更新工程师的 current_starpoint 字段。

    Args:
        session: 数据库会话
        engineer_id: 工程师 ID
        change_amount: 星点变化量
        judgment_type: 判定类型
        task_id: 关联任务 ID（可选）
        reason: 变化原因（可选）
        T_reported: 报价工时（可选）
        T_actual: 实际工时（可选）

    Returns:
        创建的星点记录
    """
    # 创建记录
    record = StarPointRecord(
        engineer_id=engineer_id,
        task_id=task_id,
        change_amount=change_amount,
        judgment_type=judgment_type,
        reason=reason,
        T_reported=T_reported,
        T_actual=T_actual,
    )
    session.add(record)

    # 更新工程师的 current_starpoint
    engineer = await session.get(User, engineer_id)
    if engineer:
        engineer.current_starpoint += change_amount
        session.add(engineer)

    await session.commit()
    await session.refresh(record)
    return record


# ============================== 星点统计 ==============================

async def get_total_starpoints(
    *,
    session: AsyncSession,
    engineer_id: uuid.UUID,
) -> int:
    """获取工程师的星点总数"""
    engineer = await session.get(User, engineer_id)
    return engineer.current_starpoint if engineer else 0


async def get_current_month_earned(
    *,
    session: AsyncSession,
    engineer_id: uuid.UUID,
) -> int:
    """获取工程师本月获得星点"""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stmt = select(func.coalesce(func.sum(StarPointRecord.change_amount), 0)).where(
        and_(
            StarPointRecord.engineer_id == engineer_id,
            StarPointRecord.created_at >= month_start,
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one()


# ============================== 排行榜 ==============================

async def get_leaderboard(
    *,
    session: AsyncSession,
    limit: int = 100,
) -> list[dict]:
    """
    获取星点排行榜

    按 current_starpoint 降序排列所有工程师。

    Args:
        session: 数据库会话
        limit: 返回记录数上限

    Returns:
        排行榜列表，每项包含 engineer_id, engineer_name, total_starpoints
    """
    stmt = (
        select(
            User.id,
            User.full_name,
            User.current_starpoint,
        )
        .where(User.role == "engineer")
        .order_by(User.current_starpoint.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.all()

    leaderboard = []
    for i, row in enumerate(rows):
        leaderboard.append({
            "engineer_id": row.id,
            "engineer_name": row.full_name,
            "total_starpoints": row.current_starpoint,
        })

    return leaderboard


async def calculate_k_coefficient(
    *,
    session: AsyncSession,
    engineer_id: uuid.UUID,
) -> float:
    """
    计算工程师的 K 系数

    从 system_param 分类的活跃规则读取分段阈值：
    - top_k: 前 top_ratio 的 K 值
    - middle_k: 中间段的 K 值
    - bottom_k: 后 bottom_ratio 的 K 值
    - top_ratio: 前百分之几（默认 0.2）
    - bottom_ratio: 后百分之几（默认 0.2）

    Args:
        session: 数据库会话
        engineer_id: 工程师 ID

    Returns:
        K 系数（默认 1.0）
    """
    # 从数据库加载 K 系数配置
    k_config = _DEFAULT_K_CONFIG.copy()
    rules, _ = await rule_repo.get_rules(
        session=session,
        category=RuleCategory.SYSTEM_PARAM,
        skip=0,
        limit=100,
    )
    for rule in rules:
        if rule.is_active:
            try:
                values = json.loads(rule.value)
                k_config.update(values)
            except (json.JSONDecodeError, TypeError):
                continue

    top_k = k_config.get("top_k", 1.2)
    middle_k = k_config.get("middle_k", 1.0)
    bottom_k = k_config.get("bottom_k", 0.7)
    top_ratio = k_config.get("top_ratio", 0.2)
    bottom_ratio = k_config.get("bottom_ratio", 0.2)

    # 获取所有工程师的排名
    stmt = (
        select(User.id, User.current_starpoint)
        .where(User.role == "engineer")
        .order_by(User.current_starpoint.desc())
    )
    result = await session.execute(stmt)
    all_engineers = list(result.all())

    if not all_engineers:
        return middle_k

    total = len(all_engineers)
    top_count = max(1, int(total * top_ratio))
    bottom_count = max(1, int(total * bottom_ratio))

    for i, row in enumerate(all_engineers):
        if row.id == engineer_id:
            if i < top_count:
                return top_k
            elif i >= total - bottom_count:
                return bottom_k
            else:
                return middle_k

    return middle_k


async def get_engineer_rank(
    *,
    session: AsyncSession,
    engineer_id: uuid.UUID,
) -> Optional[int]:
    """获取工程师在排行榜中的排名（从 1 开始）"""
    stmt = (
        select(User.id, User.current_starpoint)
        .where(User.role == "engineer")
        .order_by(User.current_starpoint.desc())
    )
    result = await session.execute(stmt)
    all_engineers = list(result.all())

    for i, row in enumerate(all_engineers):
        if row.id == engineer_id:
            return i + 1  # 排名从 1 开始

    return None
