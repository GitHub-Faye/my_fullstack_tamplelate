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


# 默认星点奖励规则（Spec §24）
# T实/T报 比例阈值和对应的星点变化
# 注意：规则按顺序检测，第一个匹配的生效
DEFAULT_STARPOINT_RULES = {
    # 提前完成：T实 ≤ 0.8 × T报 → +5
    "early_finish_ratio": 0.8,
    "early_finish_points": 5,
    # 按时完成：0.8 < T实 ≤ T报 → +3
    "on_time_ratio": 1.0,
    "on_time_points": 3,
    # 轻微超时：T报 < T实 ≤ 1.2 × T报 → -5
    "slight_overtime_ratio": 1.2,
    "slight_overtime_points": -5,
    # 显著超时：1.2 < T实 ≤ 1.5 × T报 → -10
    "moderate_overtime_ratio": 1.5,
    "moderate_overtime_points": -10,
    # 严重超时：1.5 < T实 ≤ 2.0 × T报 → -20
    "severe_overtime_ratio": 2.0,
    "severe_overtime_points": -20,
    # 极端超时：T实 > 2.0 × T报 → -30
    "extreme_overtime_points": -30,
    # 紧急任务额外奖励
    "urgent_bonus": 15,
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

    计算规则（Spec §24）：
    - T实 ≤ 0.8 × T报：提前完成，+5 星点
    - T实 ≤ T报：按时完成，+3 星点
    - T实 ≤ 1.2 × T报：超时 ≤ 20%，-5 星点
    - T实 ≤ 1.5 × T报：超时 21-50%，-10 星点
    - T实 ≤ 2 × T报：超时 51-100%，-20 星点
    - T实 > 2 × T报：超时 > 100%，-30 星点
    - 紧急任务完成：额外 +15 星点
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

    # 按 Spec §24 阈值阶梯检测（从紧到松）
    early_finish = effective_rules.get("early_finish_ratio", 0.8)
    on_time = effective_rules.get("on_time_ratio", 1.0)
    slight_overtime = effective_rules.get("slight_overtime_ratio", 1.2)
    moderate_overtime = effective_rules.get("moderate_overtime_ratio", 1.5)
    severe_overtime = effective_rules.get("severe_overtime_ratio", 2.0)

    if ratio <= early_finish:
        # 提前完成：T实 ≤ 0.8 × T报
        change_amount = effective_rules.get("early_finish_points", 5)
        reason = f"Early finish (T_actual/T_reported={ratio:.2f})"
        judgment = JudgmentType.AUTO_RATIO
    elif ratio <= on_time:
        # 按时完成：0.8 < T实 ≤ T报
        change_amount = effective_rules.get("on_time_points", 3)
        reason = f"On-time completion (T_actual/T_reported={ratio:.2f})"
        judgment = JudgmentType.AUTO_RATIO
    elif ratio <= slight_overtime:
        # 轻微超时：T报 < T实 ≤ 1.2 × T报
        change_amount = effective_rules.get("slight_overtime_points", -5)
        reason = f"Slight overtime (T_actual/T_reported={ratio:.2f})"
        judgment = JudgmentType.AUTO_RATIO
    elif ratio <= moderate_overtime:
        # 显著超时：1.2 < T实 ≤ 1.5 × T报
        change_amount = effective_rules.get("moderate_overtime_points", -10)
        reason = f"Moderate overtime (T_actual/T_reported={ratio:.2f})"
        judgment = JudgmentType.AUTO_THRESHOLD
    elif ratio <= severe_overtime:
        # 严重超时：1.5 < T实 ≤ 2.0 × T报
        change_amount = effective_rules.get("severe_overtime_points", -20)
        reason = f"Severe overtime (T_actual/T_reported={ratio:.2f})"
        judgment = JudgmentType.AUTO_THRESHOLD
    else:
        # 极端超时：T实 > 2.0 × T报
        change_amount = effective_rules.get("extreme_overtime_points", -30)
        reason = f"Extreme overtime (T_actual/T_reported={ratio:.2f})"
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
