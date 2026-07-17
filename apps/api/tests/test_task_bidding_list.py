"""
Test task status filtering for bidding tasks
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Task, TaskStatus, TaskType, User, UserRoleType
from app.core.security import get_password_hash, create_access_token


async def create_test_engineer(db_session: AsyncSession) -> User:
    """创建测试工程师用户"""
    engineer = User(
        email=f"engineer_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Engineer",
        role=UserRoleType.ENGINEER,
        is_active=True,
        is_superuser=True,
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


@pytest.mark.asyncio
async def test_get_bidding_tasks_list(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试获取竞价中的任务列表"""
    # 创建工程师和 PM
    engineer = await create_test_engineer(db_session)
    pm = await create_test_pm(db_session)

    # 创建不同状态的任务
    task1 = Task(
        name="竞价任务1",
        description="测试竞价任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.BIDDING,
        pm_id=pm.id,
        bidding_deadline=datetime.now(timezone.utc) + timedelta(days=3),
    )
    task2 = Task(
        name="竞价任务2",
        description="测试竞价任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.BIDDING,
        pm_id=pm.id,
        bidding_deadline=datetime.now(timezone.utc) + timedelta(days=5),
    )
    task3 = Task(
        name="未确认任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    task4 = Task(
        name="已确认未发布任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.CONFIRMED_UNPUBLISHED,
        pm_id=pm.id,
    )

    db_session.add(task1)
    db_session.add(task2)
    db_session.add(task3)
    db_session.add(task4)
    await db_session.commit()

    # 生成工程师 token
    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    # 获取所有任务
    response_all = await client.get(
        "/v1/tasks/?page=1&page_size=100",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_all.status_code == 200
    data_all = response_all.json()
    assert data_all["count"] == 4

    # 获取竞价中的任务
    response_bidding = await client.get(
        "/v1/tasks/?status=bidding&page=1&page_size=100",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_bidding.status_code == 200
    data_bidding = response_bidding.json()
    assert data_bidding["count"] == 2
    assert len(data_bidding["data"]) == 2

    # 验证返回的都是竞价任务
    for task in data_bidding["data"]:
        assert task["status"] == "bidding"

    # 验证竞价任务包含 bidding_deadline
    for task in data_bidding["data"]:
        assert task["bidding_deadline"] is not None


@pytest.mark.asyncio
async def test_get_bidding_tasks_with_pagination(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试竞价任务列表分页"""
    # 创建工程师和 PM
    engineer = await create_test_engineer(db_session)
    pm = await create_test_pm(db_session)

    # 创建 15 个竞价任务
    for i in range(15):
        task = Task(
            name=f"竞价任务{i}",
            description="测试竞价任务",
            task_type=TaskType.NORMAL,
            status=TaskStatus.BIDDING,
            pm_id=pm.id,
            bidding_deadline=datetime.now(timezone.utc) + timedelta(days=3),
        )
        db_session.add(task)
    await db_session.commit()

    # 生成工程师 token
    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    # 获取第一页（10条）
    response_page1 = await client.get(
        "/v1/tasks/?status=bidding&page=1&page_size=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_page1.status_code == 200
    data_page1 = response_page1.json()
    assert data_page1["count"] == 15
    assert len(data_page1["data"]) == 10
    assert data_page1["page"] == 1
    assert data_page1["total_pages"] == 2

    # 获取第二页（5条）
    response_page2 = await client.get(
        "/v1/tasks/?status=bidding&page=2&page_size=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_page2.status_code == 200
    data_page2 = response_page2.json()
    assert data_page2["count"] == 15
    assert len(data_page2["data"]) == 5


@pytest.mark.asyncio
async def test_get_tasks_filter_by_other_status(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试按其他状态过滤任务"""
    # 创建工程师和 PM
    engineer = await create_test_engineer(db_session)
    pm = await create_test_pm(db_session)

    # 创建不同状态的任务
    for i in range(3):
        task_unconfirmed = Task(
            name=f"未确认任务{i}",
            description="测试任务",
            task_type=TaskType.NORMAL,
            status=TaskStatus.UNCONFIRMED,
            pm_id=pm.id,
        )
        task_bidding = Task(
            name=f"竞价任务{i}",
            description="测试任务",
            task_type=TaskType.NORMAL,
            status=TaskStatus.BIDDING,
            pm_id=pm.id,
            bidding_deadline=datetime.now(timezone.utc) + timedelta(days=3),
        )
        db_session.add(task_unconfirmed)
        db_session.add(task_bidding)
    await db_session.commit()

    # 生成工程师 token
    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    # 获取未确认任务
    response_unconfirmed = await client.get(
        "/v1/tasks/?status=unconfirmed&page=1&page_size=100",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_unconfirmed.status_code == 200
    data_unconfirmed = response_unconfirmed.json()
    assert data_unconfirmed["count"] == 3
    for task in data_unconfirmed["data"]:
        assert task["status"] == "unconfirmed"

    # 获取竞价任务
    response_bidding = await client.get(
        "/v1/tasks/?status=bidding&page=1&page_size=100",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_bidding.status_code == 200
    data_bidding = response_bidding.json()
    assert data_bidding["count"] == 3
    for task in data_bidding["data"]:
        assert task["status"] == "bidding"


@pytest.mark.asyncio
async def test_engineer_can_view_all_bidding_tasks(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试工程师可以查看所有竞价任务（不仅是自己的）"""
    # 创建工程师和两个 PM
    engineer = await create_test_engineer(db_session)
    pm1 = await create_test_pm(db_session)
    pm2 = await create_test_pm(db_session)

    # PM1 创建竞价任务
    task1 = Task(
        name="PM1的竞价任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.BIDDING,
        pm_id=pm1.id,
        bidding_deadline=datetime.now(timezone.utc) + timedelta(days=3),
    )

    # PM2 创建竞价任务
    task2 = Task(
        name="PM2的竞价任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.BIDDING,
        pm_id=pm2.id,
        bidding_deadline=datetime.now(timezone.utc) + timedelta(days=5),
    )

    db_session.add(task1)
    db_session.add(task2)
    await db_session.commit()

    # 生成工程师 token
    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

            # 工程师查看所有竞价任务
    response = await client.get(
        "/v1/tasks/?status=bidding&page=1&page_size=100",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["data"]) == 2

    # 验证包含两个不同 PM 的任务
    pm_ids = [task["pm_id"] for task in data["data"]]
    assert str(pm1.id) in pm_ids
    assert str(pm2.id) in pm_ids
