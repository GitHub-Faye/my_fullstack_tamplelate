"""
Dashboard API 集成测试

测试三端首页数据概览 API：
- 工程师仪表板
- PM 仪表板
- 管理员仪表板
"""

import uuid
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    User,
    UserRoleType,
    Task,
    TaskStatus,
    TaskType,
    DailyReport,
    ClientResource,
    Role,
    RoleScope,
    UserRole,
    ReportStage,
)
from app.core.security import get_password_hash, create_access_token
from app.core.scopes import (
    DashboardScope,
    SalaryScope,
    TaskScope,
    BidScope,
    ReportScope,
    StarPointScope,
    ClientResourceScope,
)


async def create_test_engineer(session: AsyncSession) -> User:
    """创建测试工程师用户（含 scopes）"""
    engineer = User(
        email=f"engineer_dashboard_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Engineer",
        role=UserRoleType.ENGINEER,
        is_active=True,
        S0=10000.0,
        H0=50.0,
        T_monthly_plan=160.0,
        current_starpoint=100,
    )
    session.add(engineer)
    await session.commit()

    role = Role(name=f"engineer_role_{uuid.uuid4().hex[:8]}")
    session.add(role)
    await session.commit()

    user_role = UserRole(user_id=engineer.id, role_id=role.id)
    session.add(user_role)

    for scope in [
        TaskScope.READ,
        BidScope.CREATE, BidScope.UPDATE,
        ReportScope.CREATE, ReportScope.READ,
        StarPointScope.READ,
        SalaryScope.READ,
        DashboardScope.ENGINEER,
    ]:
        rs = RoleScope(scope=scope.value, role_id=role.id)
        session.add(rs)

    await session.commit()
    return engineer


async def create_test_pm(session: AsyncSession) -> User:
    """创建测试 PM 用户（含 scopes）"""
    pm = User(
        email=f"pm_dashboard_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test PM",
        role=UserRoleType.PM,
        is_active=True,
        S_base=8000.0,
        S_assess=2000.0,
    )
    session.add(pm)
    await session.commit()

    role = Role(name=f"pm_role_{uuid.uuid4().hex[:8]}")
    session.add(role)
    await session.commit()

    user_role = UserRole(user_id=pm.id, role_id=role.id)
    session.add(user_role)

    for scope in [
        TaskScope.READ, TaskScope.CREATE, TaskScope.UPDATE,
        ReportScope.READ,
        ClientResourceScope.READ, ClientResourceScope.CREATE,
        SalaryScope.READ,
        DashboardScope.PM,
    ]:
        rs = RoleScope(scope=scope.value, role_id=role.id)
        session.add(rs)

    await session.commit()
    return pm


async def create_test_admin(session: AsyncSession) -> User:
    """创建测试管理员用户（含 scopes）"""
    admin = User(
        email=f"admin_dashboard_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Admin",
        role=UserRoleType.ADMIN,
        is_active=True,
    )
    session.add(admin)
    await session.commit()

    role = Role(name=f"admin_{uuid.uuid4().hex[:8]}")
    session.add(role)
    await session.commit()

    user_role = UserRole(user_id=admin.id, role_id=role.id)
    session.add(user_role)

    for scope in [
        TaskScope.READ, TaskScope.CREATE, TaskScope.UPDATE, TaskScope.ADMIN,
        BidScope.READ,
        ReportScope.READ, ReportScope.ADMIN,
        StarPointScope.READ, StarPointScope.ADMIN,
        SalaryScope.READ, SalaryScope.ADMIN,
        ClientResourceScope.READ,
        DashboardScope.ADMIN,
    ]:
        rs = RoleScope(scope=scope.value, role_id=role.id)
        session.add(rs)

    await session.commit()
    return admin


@pytest.mark.asyncio
async def test_engineer_dashboard(client: AsyncClient, db_session: AsyncSession):
    """测试工程师仪表板 API"""
    engineer = await create_test_engineer(db_session)

    # 创建本月完成的任务
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

    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        "/v1/dashboard/engineer",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(engineer.id)
    assert data["current_starpoint"] == 100
    assert data["T_actual_monthly"] == 10.0
    assert data["accuracy_rate"] == 100.0


@pytest.mark.asyncio
async def test_pm_dashboard(client: AsyncClient, db_session: AsyncSession):
    """测试 PM 仪表板 API"""
    pm = await create_test_pm(db_session)

    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)

    # 今日新增客资
    client_resource = ClientResource(
        pm_id=pm.id,
        actual_count=10,
        baseline_count=8,
        date=now,
    )
    db_session.add(client_resource)

    # 昨日新增客资（环比）
    yesterday = now - timedelta(days=1)
    yesterday_resource = ClientResource(
        pm_id=pm.id,
        actual_count=5,
        baseline_count=4,
        date=yesterday,
        created_at=yesterday,
    )
    db_session.add(yesterday_resource)

    # 上月新增客资（环比）
    last_month = (now.replace(day=1) - timedelta(days=1)).replace(day=15)
    last_month_resource = ClientResource(
        pm_id=pm.id,
        actual_count=3,
        baseline_count=3,
        date=last_month,
        created_at=last_month,
    )
    db_session.add(last_month_resource)

    # 创建不同状态的任务用于分状态计数
    task_unconfirmed = Task(
        name="Unconfirmed Task",
        pm_id=pm.id,
        status=TaskStatus.UNCONFIRMED,
        task_type=TaskType.NORMAL,
        T_reported=8.0,
    )
    db_session.add(task_unconfirmed)

    task_bidding = Task(
        name="Bidding Task",
        pm_id=pm.id,
        status=TaskStatus.BIDDING,
        task_type=TaskType.NORMAL,
        T_reported=8.0,
    )
    db_session.add(task_bidding)

    task_in_progress = Task(
        name="In Progress Task",
        pm_id=pm.id,
        engineer_id=pm.id,
        status=TaskStatus.IN_PROGRESS,
        task_type=TaskType.NORMAL,
        T_reported=8.0,
    )
    db_session.add(task_in_progress)

    task_completed = Task(
        name="Completed Task",
        pm_id=pm.id,
        engineer_id=pm.id,
        status=TaskStatus.COMPLETED,
        task_type=TaskType.NORMAL,
        T_reported=8.0,
        T_actual=8.0,
    )
    db_session.add(task_completed)

    await db_session.commit()

    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        "/v1/dashboard/pm",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(pm.id)
    # 任务指标
    assert data["pm_task_count"] >= 4
    assert data["task_count_unconfirmed"] >= 1
    assert data["task_count_bidding"] >= 1
    assert data["task_count_in_progress"] >= 1
    assert data["task_count_completed"] >= 1
    assert data["task_count_paused"] == 0
    # 收入指标
    assert data["salary_preview"] == 10000.0
    assert data["salary_detail_url"] == ""


@pytest.mark.asyncio
async def test_admin_dashboard(client: AsyncClient, db_session: AsyncSession):
    """测试管理员仪表板 API"""
    admin = await create_test_admin(db_session)
    engineer = await create_test_engineer(db_session)

    # Engineer load query uses Task.status == TaskStatus.IN_PROGRESS
    # 创建进行中任务
    task = Task(
        name="Test Task",
        pm_id=uuid.uuid4(),
        engineer_id=engineer.id,
        status=TaskStatus.IN_PROGRESS,
        T_actual=10.0,
        T_reported=10.0,
        task_type=TaskType.NORMAL,
    )
    db_session.add(task)
    await db_session.commit()

    # 创建日报
    from datetime import datetime, timezone
    report = DailyReport(
        engineer_id=engineer.id,
        task_id=task.id,
        today_hours=8.0,
        current_stage=ReportStage.DEVELOPING,
        report_date=datetime.now(timezone.utc),
    )
    db_session.add(report)

    await db_session.commit()

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        "/v1/dashboard/admin",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["today_submitted_reports"] >= 1
    assert data["ongoing_tasks"] >= 1
    assert len(data["engineer_loads"]) >= 1
    assert len(data["starpoint_ranks"]) >= 1


@pytest.mark.asyncio
async def test_engineer_dashboard_unauthorized(client: AsyncClient, db_session: AsyncSession):
    """测试 PM 无权访问工程师仪表板"""
    pm = await create_test_pm(db_session)

    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        "/v1/dashboard/engineer",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_dashboard_unauthorized(client: AsyncClient, db_session: AsyncSession):
    """测试工程师无权访问管理员仪表板"""
    engineer = await create_test_engineer(db_session)

    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        "/v1/dashboard/admin",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403