"""
星点计算逻辑单元测试

测试星点自动计算的核心逻辑：
- 准确预估（+/- 10% 以内）：+10 星点
- 稍微偏差（10%-20%）：+5 星点
- 偏差较大（超过 30%）：-5 星点
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
async def test_accurate_estimation():
    """测试准确预估：T实/T报 在 0.9~1.1 之间，+10 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=10.0, T_reported=10.0)
    assert result["change_amount"] == 10
    assert result["judgment_type"] == JudgmentType.AUTO_RATIO


@pytest.mark.asyncio
async def test_accurate_estimation_low_boundary():
    """测试准确预估边界：T实/T报 = 0.9"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=9.0, T_reported=10.0)
    assert result["change_amount"] == 10
    assert result["judgment_type"] == JudgmentType.AUTO_RATIO


@pytest.mark.asyncio
async def test_accurate_estimation_high_boundary():
    """测试准确预估边界：T实/T报 = 1.1"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=11.0, T_reported=10.0)
    assert result["change_amount"] == 10
    assert result["judgment_type"] == JudgmentType.AUTO_RATIO


@pytest.mark.asyncio
async def test_slight_deviation_low():
    """测试稍微偏差：T实/T报 在 0.8~0.9 之间，+5 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=8.5, T_reported=10.0)
    assert result["change_amount"] == 5
    assert result["judgment_type"] == JudgmentType.AUTO_RATIO


@pytest.mark.asyncio
async def test_slight_deviation_high():
    """测试稍微偏差：T实/T报 在 1.1~1.2 之间，+5 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=11.5, T_reported=10.0)
    assert result["change_amount"] == 5
    assert result["judgment_type"] == JudgmentType.AUTO_RATIO


@pytest.mark.asyncio
async def test_major_deviation_low():
    """测试偏差较大：T实/T报 < 0.8，-5 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=7.0, T_reported=10.0)
    assert result["change_amount"] == -5
    assert result["judgment_type"] == JudgmentType.AUTO_THRESHOLD


@pytest.mark.asyncio
async def test_major_deviation_high():
    """测试偏差较大：T实/T报 > 1.2，-5 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=13.0, T_reported=10.0)
    assert result["change_amount"] == -5
    assert result["judgment_type"] == JudgmentType.AUTO_THRESHOLD


@pytest.mark.asyncio
async def test_urgent_task_bonus():
    """测试紧急任务额外 +15 星点"""
    task = create_test_task(task_type=TaskType.URGENT)
    result = await calculate_task_starpoints(task, T_actual=10.0, T_reported=10.0)
    # 准确预估 10 + 紧急奖励 15 = 25
    assert result["change_amount"] == 25


@pytest.mark.asyncio
async def test_urgent_task_with_deviation():
    """测试紧急任务偏差较大：-5 + 15 = 10"""
    task = create_test_task(task_type=TaskType.URGENT)
    result = await calculate_task_starpoints(task, T_actual=13.0, T_reported=10.0)
    # 偏差较大 -5 + 紧急奖励 15 = 10
    assert result["change_amount"] == 10


@pytest.mark.asyncio
async def test_no_reported_hours():
    """测试没有报价工时，返回 0 星点"""
    task = create_test_task()
    result = await calculate_task_starpoints(task, T_actual=10.0, T_reported=0)
    assert result["change_amount"] == 0
    assert result["judgment_type"] == JudgmentType.AUTO_THRESHOLD


@pytest.mark.asyncio
async def test_custom_rules():
    """测试自定义规则覆盖"""
    task = create_test_task()
    custom_rules = DEFAULT_STARPOINT_RULES.copy()
    custom_rules["accuracy_bonus"] = 20
    custom_rules["urgent_bonus"] = 30

    # 准确预估 + 紧急任务
    task.task_type = TaskType.URGENT
    result = await calculate_task_starpoints(task, T_actual=10.0, T_reported=10.0, rules=custom_rules)
    assert result["change_amount"] == 50  # 20 + 30