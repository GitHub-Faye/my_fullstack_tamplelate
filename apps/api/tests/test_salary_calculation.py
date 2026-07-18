"""
工资计算逻辑单元测试

测试工资计算的核心逻辑：
- 工程师工资：S下 = (S0 - P差额) × K
- PM 工资：S总 = S底 + S考
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User, UserRoleType, Task, TaskStatus, TaskType
from app.domains.salary.repository import (
    get_engineer_monthly_hours,
    calculate_engineer_salary,
    calculate_pm_salary,
    update_user_salary_params,
)
from app.domains.salary.calculation import calculate_user_salary


def create_engineer_user() -> User:
    """创建测试工程师用户"""
    from app.core.security import get_password_hash

    return User(
        id=uuid.uuid4(),
        email="engineer_salary_test@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Engineer",
        role=UserRoleType.ENGINEER,
        is_active=True,
        S0=10000.0,
        H0=50.0,
        T_monthly_plan=160.0,
        current_starpoint=100,
    )


def create_pm_user() -> User:
    """创建测试 PM 用户"""
    from app.core.security import get_password_hash

    return User(
        id=uuid.uuid4(),
        email="pm_salary_test@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test PM",
        role=UserRoleType.PM,
        is_active=True,
        S_base=8000.0,
        S_assess=2000.0,
        R_base=0.8,
        R_assess=0.2,
    )


@pytest.mark.asyncio
async def test_calculate_pm_salary():
    """测试 PM 工资计算：S总 = S底 + S考"""
    pm = create_pm_user()
    result = await calculate_pm_salary(pm=pm)

    assert result["S_base"] == 8000.0
    assert result["S_assess"] == 2000.0
    assert result["salary_total"] == 10000.0
    assert result["role"] == "pm"


@pytest.mark.asyncio
async def test_calculate_pm_salary_zero_values():
    """测试 PM 工资计算（参数为 0 时）"""
    pm = create_pm_user()
    pm.S_base = 0.0
    pm.S_assess = 0.0
    result = await calculate_pm_salary(pm=pm)

    assert result["salary_total"] == 0.0


@pytest.mark.asyncio
async def test_calculate_engineer_salary_accurate(db_session: AsyncSession):
    """测试工程师工资计算：准确预估（P差额=0，K=1.0）"""
    engineer = create_engineer_user()
    engineer.S0 = 10000.0
    engineer.H0 = 50.0
    engineer.current_starpoint = 100
    db_session.add(engineer)
    await db_session.commit()

    # 创建本月完成的任务（T实际 = T报价，P差额 = 0）
    task = Task(
        name="Test Task",
        pm_id=uuid.uuid4(),
        engineer_id=engineer.id,
        status=TaskStatus.COMPLETED,
        T_actual=10.0,
        T_reported=10.0,
        task_type=TaskType.NORMAL,
    )
    db_session.add(task)
    await db_session.commit()

    result = await calculate_engineer_salary(
        session=db_session,
        engineer=engineer,
        k_coefficient=1.0,
    )

    assert result["S0"] == 10000.0
    assert result["T_actual_monthly"] == 10.0
    assert result["T_reported_monthly"] == 10.0
    assert result["P_diff"] == 0.0  # 50 * (10 - 10) = 0
    assert result["k_coefficient"] == 1.0
    assert result["salary_final"] == 10000.0  # (10000 - 0) * 1.0 = 10000


@pytest.mark.asyncio
async def test_calculate_engineer_salary_with_p_diff(db_session: AsyncSession):
    """测试工程师工资计算：有工时差额时"""
    engineer = create_engineer_user()
    engineer.S0 = 10000.0
    engineer.H0 = 50.0
    db_session.add(engineer)
    await db_session.commit()

    # T实际 > T报价，P差额为正
    task = Task(
        name="Test Task",
        pm_id=uuid.uuid4(),
        engineer_id=engineer.id,
        status=TaskStatus.COMPLETED,
        T_actual=12.0,
        T_reported=10.0,
        task_type=TaskType.NORMAL,
    )
    db_session.add(task)
    await db_session.commit()

    result = await calculate_engineer_salary(
        session=db_session,
        engineer=engineer,
        k_coefficient=1.0,
    )

    # P差额 = 50 * (12 - 10) = 100
    assert result["P_diff"] == 100.0
    # 工资 = (10000 - 100) * 1.0 = 9900
    assert result["salary_final"] == 9900.0


@pytest.mark.asyncio
async def test_calculate_engineer_salary_with_k_coefficient(db_session: AsyncSession):
    """测试工程师工资计算：K 系数影响"""
    engineer = create_engineer_user()
    engineer.S0 = 10000.0
    engineer.H0 = 50.0
    db_session.add(engineer)
    await db_session.commit()

    task = Task(
        name="Test Task",
        pm_id=uuid.uuid4(),
        engineer_id=engineer.id,
        status=TaskStatus.COMPLETED,
        T_actual=10.0,
        T_reported=10.0,
        task_type=TaskType.NORMAL,
    )
    db_session.add(task)
    await db_session.commit()

    # K = 1.1（前 20%）
    result = await calculate_engineer_salary(
        session=db_session,
        engineer=engineer,
        k_coefficient=1.1,
    )

    # 工资 = (10000 - 0) * 1.1 = 11000
    assert result["salary_final"] == 11000.0


@pytest.mark.asyncio
async def test_calculate_engineer_salary_no_tasks(db_session: AsyncSession):
    """测试工程师工资计算：没有完成任务时"""
    engineer = create_engineer_user()
    engineer.S0 = 10000.0
    engineer.H0 = 50.0
    db_session.add(engineer)
    await db_session.commit()

    result = await calculate_engineer_salary(
        session=db_session,
        engineer=engineer,
        k_coefficient=1.0,
    )

    assert result["T_actual_monthly"] == 0.0
    assert result["T_reported_monthly"] == 0.0
    assert result["P_diff"] == 0.0
    # 工资 = (10000 - 0) * 1.0 = 10000
    assert result["salary_final"] == 10000.0


@pytest.mark.asyncio
async def test_calculate_engineer_salary_negative_result(db_session: AsyncSession):
    """测试工程师工资计算：负工资时取 0"""
    engineer = create_engineer_user()
    engineer.S0 = 1000.0  # 低基数
    engineer.H0 = 100.0   # 高时薪
    db_session.add(engineer)
    await db_session.commit()

    # 大量超时
    task = Task(
        name="Test Task",
        pm_id=uuid.uuid4(),
        engineer_id=engineer.id,
        status=TaskStatus.COMPLETED,
        T_actual=20.0,
        T_reported=5.0,
        task_type=TaskType.NORMAL,
    )
    db_session.add(task)
    await db_session.commit()

    result = await calculate_engineer_salary(
        session=db_session,
        engineer=engineer,
        k_coefficient=1.0,
    )

    # P差额 = 100 * (20 - 5) = 1500
    # 工资 = (1000 - 1500) * 1.0 = -500 → 取 0
    assert result["salary_final"] == 0.0


@pytest.mark.asyncio
async def test_update_user_salary_params(db_session: AsyncSession):
    """测试更新用户工资参数"""
    engineer = create_engineer_user()
    db_session.add(engineer)
    await db_session.commit()

    updated = await update_user_salary_params(
        session=db_session,
        user_id=engineer.id,
        params={"S0": 15000.0, "H0": 60.0},
    )

    assert updated is not None
    assert updated.S0 == 15000.0
    assert updated.H0 == 60.0
    # 未修改的字段保持不变
    assert updated.T_monthly_plan == 160.0


@pytest.mark.asyncio
async def test_update_user_salary_params_not_found(db_session: AsyncSession):
    """测试更新不存在的用户"""
    result = await update_user_salary_params(
        session=db_session,
        user_id=uuid.uuid4(),
        params={"S0": 15000.0},
    )
    assert result is None


@pytest.mark.asyncio
async def test_calculate_user_salary_engineer(db_session: AsyncSession):
    """测试 calculate_user_salary 分发工程师工资计算"""
    engineer = create_engineer_user()
    engineer.S0 = 10000.0
    engineer.H0 = 50.0
    engineer.current_starpoint = 100
    db_session.add(engineer)
    await db_session.commit()

    task = Task(
        name="Test Task",
        pm_id=uuid.uuid4(),
        engineer_id=engineer.id,
        status=TaskStatus.COMPLETED,
        T_actual=10.0,
        T_reported=10.0,
        task_type=TaskType.NORMAL,
    )
    db_session.add(task)
    await db_session.commit()

    result = await calculate_user_salary(session=db_session, user=engineer)

    assert result["role"] == "engineer"
    assert "salary_final" in result
    assert "k_coefficient" in result


@pytest.mark.asyncio
async def test_calculate_user_salary_pm():
    """测试 calculate_user_salary 分发 PM 工资计算"""
    pm = create_pm_user()
    result = await calculate_user_salary(session=None, user=pm)  # type: ignore

    assert result["role"] == "pm"
    assert result["salary_total"] == 10000.0