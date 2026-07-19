"""
系统规则模块数据访问层（Repository）

负责规则配置相关的数据库操作：CRUD、查询等。
"""

import uuid
from typing import Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import SystemRule, RuleCategory, AuditLog
from app.core.db_utils import paginated_query
from app.domains.system_rule.schemas import SystemRuleCreate, SystemRuleUpdate


# ============================== SystemRule CRUD ==============================

async def get_rule(
    *,
    session: AsyncSession,
    rule_id: uuid.UUID,
) -> SystemRule | None:
    """根据 ID 获取规则"""
    return await session.get(SystemRule, rule_id)


async def get_rules(
    *,
    session: AsyncSession,
    category: RuleCategory | None = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[list[SystemRule], int]:
    """
    获取规则列表（分页，可选按分类过滤）

    Args:
        session: 数据库会话
        category: 规则分类（可选）
        skip: 跳过记录数
        limit: 返回记录数上限

    Returns:
        (规则列表, 总数) 元组
    """
    conditions = []
    if category is not None:
        conditions.append(SystemRule.category == category)

    return await paginated_query(
        session=session,
        model=SystemRule,
        skip=skip,
        limit=limit,
        conditions=conditions or None,
        order_by=SystemRule.created_at.desc(),
    )


async def create_rule(
    *,
    session: AsyncSession,
    rule_in: SystemRuleCreate,
) -> SystemRule:
    """
    创建规则

    Args:
        session: 数据库会话
        rule_in: 规则创建请求

    Returns:
        创建的规则对象
    """
    rule = SystemRule(
        category=rule_in.category,
        name=rule_in.name,
        applies_to=rule_in.applies_to,
        value=rule_in.value,
        is_public=rule_in.is_public,
        is_active=rule_in.is_active,
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


async def update_rule(
    *,
    session: AsyncSession,
    db_rule: SystemRule,
    rule_in: SystemRuleUpdate,
) -> SystemRule:
    """
    更新规则

    Args:
        session: 数据库会话
        db_rule: 现有规则对象
        rule_in: 规则更新请求

    Returns:
        更新后的规则对象
    """
    update_data = rule_in.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(db_rule, field, value)
    session.add(db_rule)
    await session.commit()
    await session.refresh(db_rule)
    return db_rule


async def delete_rule(
    *,
    session: AsyncSession,
    db_rule: SystemRule,
) -> None:
    """
    删除规则

    Args:
        session: 数据库会话
        db_rule: 要删除的规则对象
    """
    await session.delete(db_rule)
    await session.commit()


# ============================== 审计日志 ==============================

async def create_rule_audit_log(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    action: str,
    target_id: str | None = None,
    details: str | None = None,
) -> AuditLog:
    """创建规则操作审计日志"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        target_type="system_rule",
        target_id=target_id,
        details=details,
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def get_rule_audit_logs(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[list[AuditLog], int]:
    """获取规则操作审计日志列表（分页）"""
    return await paginated_query(
        session=session,
        model=AuditLog,
        skip=skip,
        limit=limit,
        conditions=[AuditLog.target_type == "system_rule"],
        order_by=AuditLog.created_at.desc(),
    )

DEFAULT_RULES = [
    # 星点奖励规则
    SystemRuleCreate(
        category=RuleCategory.STARPOINT_REWARD,
        name="准确预估奖励",
        applies_to="engineer",
        value='{"accuracy_bonus": 10, "accuracy_threshold_high": 1.1, "accuracy_threshold_low": 0.9}',
        is_public=True,
        is_active=True,
    ),
    SystemRuleCreate(
        category=RuleCategory.STARPOINT_REWARD,
        name="稍微偏差奖励",
        applies_to="engineer",
        value='{"slight_deviation": 5, "deviation_threshold_high": 1.2, "deviation_threshold_low": 0.8}',
        is_public=True,
        is_active=True,
    ),
    SystemRuleCreate(
        category=RuleCategory.STARPOINT_REWARD,
        name="偏差较大扣分",
        applies_to="engineer",
        value='{"major_deviation": -5}',
        is_public=True,
        is_active=True,
    ),
    SystemRuleCreate(
        category=RuleCategory.STARPOINT_REWARD,
        name="紧急任务奖励",
        applies_to="engineer",
        value='{"urgent_bonus": 15}',
        is_public=True,
        is_active=True,
    ),
    # 完成判定规则
    SystemRuleCreate(
        category=RuleCategory.COMPLETION_JUDGMENT,
        name="完成判定阈值",
        applies_to="engineer",
        value='{"accuracy_threshold_high": 1.1, "accuracy_threshold_low": 0.9, "deviation_threshold_high": 1.2, "deviation_threshold_low": 0.8}',
        is_public=False,
        is_active=True,
    ),
    # 工资公式参数
    SystemRuleCreate(
        category=RuleCategory.SALARY_FORMULA,
        name="工程师工资公式",
        applies_to="engineer",
        value='{"formula": "S_final = (S0 - P_diff) * K", "description": "S0: 月度工资基数, P_diff: 工时差额, K: 星点系数"}',
        is_public=True,
        is_active=True,
    ),
    SystemRuleCreate(
        category=RuleCategory.SALARY_FORMULA,
        name="PM 工资公式",
        applies_to="pm",
        value='{"formula": "S_total = S_base + S_assess", "description": "S_base: 底薪, S_assess: 考核部分"}',
        is_public=True,
        is_active=True,
    ),
    # 系统参数
    SystemRuleCreate(
        category=RuleCategory.SYSTEM_PARAM,
        name="星点系数分段",
        applies_to="engineer",
        value='{"top_20_percent": 1.1, "middle_60_percent": 1.0, "bottom_20_percent": 0.9}',
        is_public=False,
        is_active=True,
    ),
]


async def seed_default_rules(
    *,
    session: AsyncSession,
) -> int:
    """
    预置默认规则

    检查是否已有规则，如无则写入默认规则。

    Args:
        session: 数据库会话

    Returns:
        创建的规则数量
    """
    stmt = select(func.count()).select_from(SystemRule)
    result = await session.execute(stmt)
    count = result.scalar_one()

    if count > 0:
        return 0

    created = 0
    for rule_in in DEFAULT_RULES:
        await create_rule(session=session, rule_in=rule_in)
        created += 1

    return created
