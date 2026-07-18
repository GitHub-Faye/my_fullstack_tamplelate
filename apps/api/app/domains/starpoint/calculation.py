"""
星点计算逻辑模块

提供星点自动计算功能：
- 任务完成时根据 T实/T报 比例自动计算星点变化
- 紧急任务额外星点奖励
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Task, TaskType, JudgmentType, StarPointRecord
from app.domains.starpoint import repository as starpoint_repo


# 默认星点奖励规则
# 可以从 SystemRule（category=starpoint_reward）读取，此处提供默认值
DEFAULT_STARPOINT_RULES = {
    "accuracy_bonus": 10,       # 准确预估（+/- 10% 以内）
    "slight_deviation": 5,      # 稍微偏差（10%-20%）
    "major_deviation": -5,      # 偏差较大（超过 30%）
    "urgent_bonus": 15,         # 紧急任务额外奖励
    "accuracy_threshold_high": 1.1,   # 准确预估上限
    "accuracy_threshold_low": 0.9,    # 准确预估下限
    "deviation_threshold_high": 1.2,  # 稍微偏差上限
    "deviation_threshold_low": 0.8,   # 稍微偏差下限
}


async def calculate_task_starpoints(
    task: Task,
    T_actual: float,
    T_reported: float,
    rules: Optional[dict] = None,
) -> dict:
    """
    根据任务完成数据计算星点变化

    Args:
        task: 完成任务对象
        T_actual: 实际工时
        T_reported: 报价工时
        rules: 可选的自定义规则覆盖

    Returns:
        dict: {
            "change_amount": int,
            "reason": str,
            "judgment_type": JudgmentType,
        }

    计算规则：
    - T实/T报 比例在 0.9~1.1（准确预估）：+10 星点
    - 比例在 0.8~0.9 或 1.1~1.2（稍微偏差）：+5 星点
    - 比例 < 0.8 或 > 1.2（偏差较大）：-5 星点
    - 紧急任务额外 +15 星点
    """
    effective_rules = rules or DEFAULT_STARPOINT_RULES.copy()

    # 没有报价工时，无法计算
    if not T_reported or T_reported <= 0:
        return {
            "change_amount": 0,
            "reason": "No reported hours available for starpoint calculation",
            "judgment_type": JudgmentType.AUTO_THRESHOLD,
        }

    ratio = T_actual / T_reported

    # 确定精确定级别
    threshold_high = effective_rules.get("accuracy_threshold_high", 1.1)
    threshold_low = effective_rules.get("accuracy_threshold_low", 0.9)
    dev_high = effective_rules.get("deviation_threshold_high", 1.2)
    dev_low = effective_rules.get("deviation_threshold_low", 0.8)

    if threshold_low <= ratio <= threshold_high:
        # 准确预估
        change_amount = effective_rules.get("accuracy_bonus", 10)
        reason = f"Accurate estimation (T_actual/T_reported={ratio:.2f})"
        judgment = JudgmentType.AUTO_RATIO
    elif dev_low <= ratio < threshold_low or threshold_high < ratio <= dev_high:
        # 稍微偏差
        change_amount = effective_rules.get("slight_deviation", 5)
        reason = f"Slight deviation (T_actual/T_reported={ratio:.2f})"
        judgment = JudgmentType.AUTO_RATIO
    else:
        # 偏差较大
        change_amount = effective_rules.get("major_deviation", -5)
        reason = f"Major deviation (T_actual/T_reported={ratio:.2f})"
        judgment = JudgmentType.AUTO_THRESHOLD

    # 紧急任务额外奖励
    if task.task_type == TaskType.URGENT:
        urgent_bonus = effective_rules.get("urgent_bonus", 15)
        change_amount += urgent_bonus
        reason += f" + urgent task bonus ({urgent_bonus})"

    return {
        "change_amount": change_amount,
        "reason": reason,
        "judgment_type": judgment,
    }


async def trigger_starpoint_calculation(
    session: AsyncSession,
    task: Task,
    engineer_id: Optional[str] = None,
) -> Optional[StarPointRecord]:
    """
    任务完成时触发星点自动计算

    应在任务状态变为 COMPLETED 后调用。

    Args:
        session: 数据库会话
        task: 已完成的任务
        engineer_id: 执行任务的工程师 ID（默认取 task.engineer_id）

    Returns:
        创建的星点记录，或 None（如果无法计算）
    """
    if task.status.value != "completed":
        return None

    actual_engineer_id = engineer_id or task.engineer_id
    if not actual_engineer_id:
        return None

    T_actual = task.T_actual or 0.0
    T_reported = task.T_reported or 0.0

    # 计算星点
    result = await calculate_task_starpoints(
        task=task,
        T_actual=T_actual,
        T_reported=T_reported,
    )

    # 创建星点记录
    record = await starpoint_repo.create_starpoint_record(
        session=session,
        engineer_id=actual_engineer_id,
        change_amount=result["change_amount"],
        judgment_type=result["judgment_type"],
        task_id=task.id,
        reason=result["reason"],
        T_reported=T_reported,
        T_actual=T_actual,
    )

    return record
