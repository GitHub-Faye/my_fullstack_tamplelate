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

from app.core.models import User, UserRoleType, Task, TaskStatus, TaskType, ClientResource
from app.domains.salary.repository import (
    update_user_salary_params,
)
from app.domains.salary.service import (
    calculate_engineer_salary,
    calculate_pm_salary,
    calculate_user_salary,
)
from app.domains.salary.schemas import EngineerSalaryDetail, PMSalaryDetail, SalaryParamsUpdate
from app.domains.shared.queries import get_engineer_monthly_hours


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
async def test_calculate_pm_salary(db_session: AsyncSession):
    """测试 PM 工资计算：S总 = S底 + S考"""
    pm = create_pm_user()
    db_session.add(pm)
    await db_session.commit()
    result = await calculate_pm_salary(pm=pm)

    assert result.S_base == 8000.0
    assert result.S_assess == 2000.0
    assert result.salary_total == 10000.0
    assert result.role == "pm"



@pytest.mark.asyncio
async def test_calculate_pm_salary_zero_values(db_session: AsyncSession):
    """测试 PM 工资计算（参数为 0 时）"""
    pm = create_pm_user()
    pm.S_base = 0.0
    pm.S_assess = 0.0
    db_session.add(pm)
    await db_session.commit()
    result = await calculate_pm_salary(pm=pm)

    assert result.salary_total == 0.0


@pytest.mark.asyncio
async def test_calculate_engineer_salary_accurate(db_session: AsyncSession):
    """测试工程师工资计算：准确预估（P差额=0，K=1.0）"""
    engineer = create_engineer_user()
    engineer.S0 = 10000.0
    engineer.H0 = 50.0
    engineer.current_starpoint = 100
    db_session.add(engineer)
    await db_session.commit()

    # 创建本月完成的任务（T实际 = T报价 = 10h，T有效 = 10h）
    task = Task(
        name="Test Task",
        pm_id=uuid.uuid4(),
        engineer_id=engineer.id,
        status=TaskStatus.COMPLETED,
        T_actual=10.0,
        T_reported=10.0,
        T_effective=10.0,
        task_type=TaskType.NORMAL,
    )
    db_session.add(task)
    await db_session.commit()

    result = await calculate_engineer_salary(
        session=db_session,
        engineer=engineer,
        k_coefficient=1.0,
    )

    # H0 = S0 / T月计划 = 10000 / 160 = 62.5
    assert result.S0 == 10000.0
    assert result.H0 == 62.5
    assert result.T_monthly_plan == 160.0
    assert result.T_actual_monthly == 10.0
    assert result.T_reported_monthly == 10.0
    assert result.T_effective == 10.0
    # P差额 = max(0, 160 - 10) * 62.5 = 150 * 62.5 = 9375
    assert result.P_diff == 9375.0
    assert result.k_coefficient == 1.0
    # 工资 = max(5000, (10000 - 9375) * 1.0) = max(5000, 625) = 5000
    assert result.salary_final == 5000.0


@pytest.mark.asyncio
async def test_calculate_engineer_salary_with_p_diff(db_session: AsyncSession):
    """测试工程师工资计算：有工时差额时"""
    engineer = create_engineer_user()
    engineer.S0 = 10000.0
    engineer.H0 = 50.0
    db_session.add(engineer)
    await db_session.commit()

    # T实际 = 12h, T报 = 10h, T有效 = 10h (min)
    task = Task(
        name="Test Task",
        pm_id=uuid.uuid4(),
        engineer_id=engineer.id,
        status=TaskStatus.COMPLETED,
        T_actual=12.0,
        T_reported=10.0,
        T_effective=10.0,
        task_type=TaskType.NORMAL,
    )
    db_session.add(task)
    await db_session.commit()

    result = await calculate_engineer_salary(
        session=db_session,
        engineer=engineer,
        k_coefficient=1.0,
    )

    # H0 = 10000 / 160 = 62.5
    # P差额 = max(0, 160 - 10) * 62.5 = 9375
    assert result.P_diff == 9375.0
    # 工资 = max(5000, (10000 - 9375) * 1.0) = max(5000, 625) = 5000
    assert result.salary_final == 5000.0


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
        T_effective=10.0,
        task_type=TaskType.NORMAL,
    )
    db_session.add(task)
    await db_session.commit()

    # K = 1.2（前 20%，按新 PRD 系数）
    result = await calculate_engineer_salary(
        session=db_session,
        engineer=engineer,
        k_coefficient=1.2,
    )

    # H0 = 10000 / 160 = 62.5
    # P差额 = max(0, 160 - 10) * 62.5 = 9375
    # 工资 = max(5000, (10000 - 9375) * 1.2) = max(5000, 750) = 5000
    assert result.salary_final == 5000.0


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

    assert result.T_actual_monthly == 0.0
    assert result.T_reported_monthly == 0.0
    assert result.T_effective == 0.0
    # H0 = 10000 / 160 = 62.5
    # P差额 = max(0, 160 - 0) * 62.5 = 10000
    # 工资 = max(5000, (10000 - 10000) * 1.0) = max(5000, 0) = 5000
    assert result.salary_final == 5000.0


@pytest.mark.asyncio
async def test_calculate_engineer_salary_negative_result(db_session: AsyncSession):
    """测试工程师工资计算：低于保底时取 5000"""
    engineer = create_engineer_user()
    engineer.S0 = 8000.0
    engineer.T_monthly_plan = 160.0
    db_session.add(engineer)
    await db_session.commit()

    # 少量完成
    task = Task(
        name="Test Task",
        pm_id=uuid.uuid4(),
        engineer_id=engineer.id,
        status=TaskStatus.COMPLETED,
        T_actual=20.0,
        T_reported=5.0,
        T_effective=5.0,
        task_type=TaskType.NORMAL,
    )
    db_session.add(task)
    await db_session.commit()

    result = await calculate_engineer_salary(
        session=db_session,
        engineer=engineer,
        k_coefficient=1.0,
    )

    # H0 = 8000 / 160 = 50
    # P差额 = max(0, 160 - 5) * 50 = 7750
    # 工资 = max(5000, (8000 - 7750) * 1.0) = max(5000, 250) = 5000
    assert result.salary_final == 5000.0


@pytest.mark.asyncio
async def test_calculate_engineer_salary_prd_example(db_session: AsyncSession):
    """测试 PRD 示例：S0=8000, T月计划=150h, T有效=140h, K=1.0"""
    engineer = create_engineer_user()
    engineer.S0 = 8000.0
    engineer.T_monthly_plan = 150.0
    engineer.current_starpoint = 100
    db_session.add(engineer)
    await db_session.commit()

    task = Task(
        name="Test Task",
        pm_id=uuid.uuid4(),
        engineer_id=engineer.id,
        status=TaskStatus.COMPLETED,
        T_actual=150.0,
        T_reported=140.0,
        T_effective=140.0,
        task_type=TaskType.NORMAL,
    )
    db_session.add(task)
    await db_session.commit()

    result = await calculate_engineer_salary(
        session=db_session,
        engineer=engineer,
        k_coefficient=1.0,
    )

    # H0 = 8000 / 150 ≈ 53.3333
    assert result.H0 == pytest.approx(8000 / 150, rel=1e-4)
    # P差额 = max(0, 150 - 140) * 53.3333 ≈ 533.333
    expected_P_diff = (150 - 140) * (8000 / 150)
    assert result.P_diff == pytest.approx(expected_P_diff, rel=1e-4)
    # 工资 = max(5000, (8000 - 533.333) * 1.0) = 7466.67
    expected_salary = max(5000, (8000 - expected_P_diff) * 1.0)
    assert result.salary_final == pytest.approx(expected_salary, rel=1e-4)


@pytest.mark.asyncio
async def test_update_user_salary_params(db_session: AsyncSession):
    """测试更新用户工资参数"""
    engineer = create_engineer_user()
    db_session.add(engineer)
    await db_session.commit()

    updated = await update_user_salary_params(
        session=db_session,
        user_id=engineer.id,
        params=SalaryParamsUpdate(S0=15000.0, H0=60.0),
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
        params=SalaryParamsUpdate(S0=15000.0),
    )
    assert result is None


@pytest.mark.asyncio
async def test_calculate_user_salary_engineer(db_session: AsyncSession):
    """测试 calculate_user_salary 分发工程师工资计算"""
    engineer = create_engineer_user()
    engineer.S0 = 10000.0
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
        T_effective=10.0,
        task_type=TaskType.NORMAL,
    )
    db_session.add(task)
    await db_session.commit()

    result = await calculate_user_salary(session=db_session, user=engineer)

    assert result.role == "engineer"
    assert hasattr(result, "salary_final")
    assert hasattr(result, "k_coefficient")


@pytest.mark.asyncio
async def test_calculate_user_salary_pm(db_session: AsyncSession):
    """测试 calculate_user_salary 分发 PM 工资计算"""
    pm = create_pm_user()
    db_session.add(pm)
    await db_session.commit()
    result = await calculate_user_salary(session=db_session, user=pm)

    assert result.role == "pm"
    assert isinstance(result, PMSalaryDetail)
    assert result.salary_total == 10000.0