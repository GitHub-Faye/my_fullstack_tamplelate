"""
Bid API 集成测试

测试工程师竞价报价功能：提交报价、修改报价、查看报价列表
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Task, TaskStatus, TaskType, User, UserRoleType
from app.core.security import get_password_hash, create_access_token


# ==================== 测试数据准备 ====================

async def create_test_engineer(db_session: AsyncSession) -> User:
    """创建测试工程师用户"""
    engineer = User(
        email=f"engineer_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Engineer",
        role=UserRoleType.ENGINEER,
        is_active=True,
        is_superuser=True,  # 添加超管标志以获取权限
    )
    db_session.add(engineer)
    await db_session.commit()
    await db_session.refresh(engineer)
    return engineer


async def create_test_pm(db_session: AsyncSession) -> User:
    """创建测试 PM 用户"""
    pm = User(
        email=f"pm_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test PM",
        role=UserRoleType.PM,
        is_active=True,
    )
    db_session.add(pm)
    await db_session.commit()
    await db_session.refresh(pm)
    return pm


async def create_test_admin(db_session: AsyncSession) -> User:
    """创建测试管理员用户"""
    admin = User(
        email=f"admin_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Admin",
        role=UserRoleType.ADMIN,
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


async def create_bidding_task(db_session: AsyncSession, pm: User) -> Task:
    """创建竞价中的任务"""
    task = Task(
        name="竞价任务",
        description="测试竞价任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.BIDDING,
        pm_id=pm.id,
        bidding_deadline=datetime.now(timezone.utc) + timedelta(days=3),
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


# ==================== 测试用例：提交报价 ====================

@pytest.mark.asyncio
async def test_create_bid_success(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试工程师成功提交报价"""
    # 创建工程师和 PM
    engineer = await create_test_engineer(db_session)
    pm = await create_test_pm(db_session)

    # 创建竞价中的任务
    task = await create_bidding_task(db_session, pm)

    # 生成工程师 token
    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    # 提交报价
    response = await client.post(
        f"/v1/tasks/{task.id}/bids",
        json={"T_reported": 8.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["T_reported"] == 8.0
    assert data["amount"] == 800.0  # 8.0 * 100
    assert data["task_id"] == str(task.id)
    assert data["engineer_id"] == str(engineer.id)


@pytest.mark.asyncio
async def test_create_bid_not_bidding_task_fails(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试无法对非竞价中的任务报价"""
    # 创建工程师和 PM
    engineer = await create_test_engineer(db_session)
    pm = await create_test_pm(db_session)

    # 创建未确认的任务
    task = Task(
        name="未确认任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 生成工程师 token
    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    # 尝试报价
    response = await client.post(
        f"/v1/tasks/{task.id}/bids",
        json={"T_reported": 8.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_bid_passed_deadline_fails(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试无法在竞价截止时间后报价"""
    # 创建工程师和 PM
    engineer = await create_test_engineer(db_session)
    pm = await create_test_pm(db_session)

    # 创建已过截止时间的竞价任务
    task = Task(
        name="过期竞价任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.BIDDING,
        pm_id=pm.id,
        bidding_deadline=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 生成工程师 token
    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    # 尝试报价
    response = await client.post(
        f"/v1/tasks/{task.id}/bids",
        json={"T_reported": 8.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


# ==================== 测试用例：修改报价 ====================

@pytest.mark.asyncio
async def test_update_bid_success(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试工程师成功修改报价"""
    # 创建工程师和 PM
    engineer = await create_test_engineer(db_session)
    pm = await create_test_pm(db_session)

    # 创建竞价中的任务
    task = await create_bidding_task(db_session, pm)

    # 先提交报价
    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    create_response = await client.post(
        f"/v1/tasks/{task.id}/bids",
        json={"T_reported": 8.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    bid_id = create_response.json()["id"]

    # 修改报价
    update_response = await client.put(
        f"/v1/tasks/{task.id}/bids/{bid_id}",
        json={"T_reported": 10.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["T_reported"] == 10.0
    assert data["amount"] == 1000.0  # 10.0 * 100


@pytest.mark.asyncio
async def test_update_other_engineer_bid_fails(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试无法修改其他工程师的报价"""
    # 创建两个工程师和 PM
    engineer1 = await create_test_engineer(db_session)
    engineer2 = await create_test_engineer(db_session)
    pm = await create_test_pm(db_session)

    # 创建竞价中的任务
    task = await create_bidding_task(db_session, pm)

    # 工程师1提交报价
    token1 = create_access_token(
        subject=str(engineer1.id),
        expires_delta=timedelta(minutes=30),
    )

    create_response = await client.post(
        f"/v1/tasks/{task.id}/bids",
        json={"T_reported": 8.0},
        headers={"Authorization": f"Bearer {token1}"},
    )
    bid_id = create_response.json()["id"]

    # 工程师2尝试修改
    token2 = create_access_token(
        subject=str(engineer2.id),
        expires_delta=timedelta(minutes=30),
    )

    update_response = await client.put(
        f"/v1/tasks/{task.id}/bids/{bid_id}",
        json={"T_reported": 10.0},
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert update_response.status_code == 403


# ==================== 测试用例：查看报价 ====================

@pytest.mark.asyncio
async def test_read_bids_by_task(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试查看任务的报价列表"""
    # 创建工程师和 PM
    engineer = await create_test_engineer(db_session)
    pm = await create_test_pm(db_session)

    # 创建竞价中的任务
    task = await create_bidding_task(db_session, pm)

    # 提交报价
    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    await client.post(
        f"/v1/tasks/{task.id}/bids",
        json={"T_reported": 8.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    # 查看报价列表
    response = await client.get(
        f"/v1/tasks/{task.id}/bids",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert len(data["data"]) == 1
    # engineer_name 应从 User.full_name 填充，而非显示 id
    assert data["data"][0]["engineer_name"] == "Test Engineer"


@pytest.mark.asyncio
async def test_read_my_bids(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试工程师查看自己的报价列表"""
    # 创建工程师和 PM
    engineer = await create_test_engineer(db_session)
    pm = await create_test_pm(db_session)

    # 创建两个竞价任务
    task1 = await create_bidding_task(db_session, pm)
    task2 = await create_bidding_task(db_session, pm)

    # 提交两个报价
    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    await client.post(
        f"/v1/tasks/{task1.id}/bids",
        json={"T_reported": 8.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    await client.post(
        f"/v1/tasks/{task2.id}/bids",
        json={"T_reported": 10.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    # 查看我的报价
    response = await client.get(
        "/v1/bids/my",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["data"]) == 2


# ==================== 测试用例：权限检查 ====================

@pytest.mark.asyncio
async def test_pm_cannot_create_bid(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试 PM 无法提交报价"""
    # 创建 PM
    pm = await create_test_pm(db_session)

    # 创建竞价中的任务
    task = await create_bidding_task(db_session, pm)

    # 生成 PM token
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    # PM 尝试报价
    response = await client.post(
        f"/v1/tasks/{task.id}/bids",
        json={"T_reported": 8.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    # PM 没有 bid:create 权限
    assert response.status_code == 403
