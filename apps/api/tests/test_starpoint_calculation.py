"""
星点计算逻辑单元测试

测试星点自动计算的核心逻辑（Spec §24）：
- T实 ≤ 0.8 × T报（提前完成）：+5 星点
- T实 ≤ T报（按时完成）：+3 星点
- T实 ≤ 1.2 × T报（超时 ≤ 20%）：-5 星点
- T实 ≤ 1.5 × T报（超时 21-50%）：-10 星点
- T实 ≤ 2 × T报（超时 51-100%）：-20 星点
- T实 > 2 × T报（超时 > 100%）：-30 星点
- 紧急任务额外 +15 星点
"""

import pytest
from app.core.models import Task, TaskStatus, TaskType, JudgmentType
from app.domains.starpoint.calculation import calculate_task_starpoints, DEFAULT_STARPOINT_RULES


def create_test_task(task_type: TaskType = TaskType.NORMAL, status: TaskStatus = TaskStatus.COMPLETED) -> Task:
    """创建测试任务"""
    return Task(
        name="Test Task",
        task_type=task_type,
        status=status,
        pm_id="00000000-0000-0000-0000-000000000001",
        T_reported=10.0,
        T_actual=9.5,
    )


@pytest.mark.asyncio
async def test_early_finish():
    """提前完成：T实/T报 ≤ 0.8，+5 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=8.0, T_reported=10.0)
    assert result["change_amount"] == 5
    assert result["judgment_type"] == JudgmentType.AUTO_RATIO


@pytest.mark.asyncio
async def test_early_finish_boundary():
    """提前完成边界：T实/T报 = 0.8"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=8.0, T_reported=10.0)
    assert result["change_amount"] == 5


@pytest.mark.asyncio
async def test_on_time_completion():
    """按时完成：0.8 < T实/T报 ≤ 1.0，+3 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=9.0, T_reported=10.0)
    assert result["change_amount"] == 3
    assert result["judgment_type"] == JudgmentType.AUTO_RATIO


@pytest.mark.asyncio
async def test_on_time_completion_exact():
    """按时完成边界：T实/T报 = 1.0"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=10.0, T_reported=10.0)
    assert result["change_amount"] == 3


@pytest.mark.asyncio
async def test_on_time_completion_above_early():
    """按时完成边界：T实/T报 = 0.81"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=8.1, T_reported=10.0)
    assert result["change_amount"] == 3


@pytest.mark.asyncio
async def test_slight_overtime():
    """轻微超时：1.0 < T实/T报 ≤ 1.2，-5 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=11.0, T_reported=10.0)
    assert result["change_amount"] == -5
    assert result["judgment_type"] == JudgmentType.AUTO_RATIO


@pytest.mark.asyncio
async def test_slight_overtime_boundary():
    """轻微超时边界：T实/T报 = 1.2"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=12.0, T_reported=10.0)
    assert result["change_amount"] == -5


@pytest.mark.asyncio
async def test_moderate_overtime():
    """显著超时：1.2 < T实/T报 ≤ 1.5，-10 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=13.0, T_reported=10.0)
    assert result["change_amount"] == -10
    assert result["judgment_type"] == JudgmentType.AUTO_THRESHOLD


@pytest.mark.asyncio
async def test_moderate_overtime_boundary():
    """显著超时边界：T实/T报 = 1.5"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=15.0, T_reported=10.0)
    assert result["change_amount"] == -10


@pytest.mark.asyncio
async def test_severe_overtime():
    """严重超时：1.5 < T实/T报 ≤ 2.0，-20 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=18.0, T_reported=10.0)
    assert result["change_amount"] == -20
    assert result["judgment_type"] == JudgmentType.AUTO_THRESHOLD


@pytest.mark.asyncio
async def test_severe_overtime_boundary():
    """严重超时边界：T实/T报 = 2.0"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=20.0, T_reported=10.0)
    assert result["change_amount"] == -20


@pytest.mark.asyncio
async def test_extreme_overtime():
    """极端超时：T实/T报 > 2.0，-30 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=25.0, T_reported=10.0)
    assert result["change_amount"] == -30
    assert result["judgment_type"] == JudgmentType.AUTO_THRESHOLD


@pytest.mark.asyncio
async def test_urgent_task_bonus():
    """紧急任务：准确预估 3 + 紧急奖励 15 = 18 星点"""
    task = create_test_task(task_type=TaskType.URGENT)
    result = await calculate_task_starpoints(task, T_actual=10.0, T_reported=10.0)
    assert result["change_amount"] == 18


@pytest.mark.asyncio
async def test_urgent_task_with_deviation():
    """紧急任务显著超时：-10 + 15 = 5 星点"""
    task = create_test_task(task_type=TaskType.URGENT)
    result = await calculate_task_starpoints(task, T_actual=13.0, T_reported=10.0)
    assert result["change_amount"] == 5


@pytest.mark.asyncio
async def test_no_reported_hours():
    """没有报价工时，返回 0 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=10.0, T_reported=0)
    assert result["change_amount"] == 0
    assert result["judgment_type"] == JudgmentType.AUTO_THRESHOLD


@pytest.mark.asyncio
async def test_custom_rules():
    """自定义规则覆盖"""
    task = create_test_task()
    custom_rules = DEFAULT_STARPOINT_RULES.copy()
    custom_rules["on_time_points"] = 10
    custom_rules["urgent_bonus"] = 30

    # 按时完成 + 紧急任务
    task.task_type = TaskType.URGENT
    result = await calculate_task_starpoints(task, T_actual=10.0, T_reported=10.0, rules=custom_rules)
    assert result["change_amount"] == 40  # 10 + 30