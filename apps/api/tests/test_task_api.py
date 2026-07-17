"""
Task API 集成测试

测试 PM 任务管理的核心功能：创建、查询、更新、删除
"""

import uuid
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Task, TaskStatus, TaskType, User, UserRoleType
from app.core.security import get_password_hash
from tests.conftest import client as async_client_fixture


# ==================== 测试数据准备 ====================

async def create_test_pm(session: AsyncSession) -> User:
    """创建测试 PM 用户"""
    pm = User(
        email=f"pm_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test PM",
        role=UserRoleType.PM,
        is_active=True,
    )
    session.add(pm)
    await session.commit()
    await session.refresh(pm)
    return pm


async def create_test_admin(session: AsyncSession) -> User:
    """创建测试管理员用户"""
    admin = User(
        email=f"admin_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Admin",
        role=UserRoleType.ADMIN,
        is_active=True,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


async def create_test_engineer(session: AsyncSession) -> User:
    """创建测试工程师用户"""
    engineer = User(
        email=f"engineer_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Engineer",
        role=UserRoleType.ENGINEER,
        is_active=True,
    )
    session.add(engineer)
    await session.commit()
    await session.refresh(engineer)
    return engineer


# ==================== 测试用例 ====================

@pytest.mark.asyncio
async def test_create_task_as_pm(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试 PM 创建任务"""
    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 登录获取 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    # 创建任务
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "name": "测试任务",
            "description": "这是一个测试任务",
            "task_type": "normal",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试任务"
    assert data["status"] == "unconfirmed"
    assert data["pm_id"] == str(pm.id)
    assert data["task_type"] == "normal"


@pytest.mark.asyncio
async def test_create_task_as_engineer_fails(client: AsyncClient, session: AsyncSession) -> None:
    """测试工程师无法创建任务"""
    # 创建工程师用户
    engineer = await create_test_engineer(session)

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    # 尝试创建任务
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "name": "测试任务",
            "description": "这是一个测试任务",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # 工程师不应该有 task:create 权限
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_read_tasks_as_pm(client: AsyncClient, session: AsyncSession) -> None:
    """测试 PM 查看自己的任务列表"""
    # 创建 PM 用户
    pm = await create_test_pm(session)

    # 创建任务
    task = Task(
        name="PM 的任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    session.add(task)
    await session.commit()

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    # 查询任务列表
    response = await client.get(
        "/api/v1/tasks/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["name"] == "PM 的任务"
    assert data["data"][0]["pm_id"] == str(pm.id)


@pytest.mark.asyncio
async def test_read_task_by_id(client: AsyncClient, session: AsyncSession) -> None:
    """测试查看任务详情"""
    # 创建 PM 用户
    pm = await create_test_pm(session)

    # 创建任务
    task = Task(
        name="测试任务详情",
        description="详细描述",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    # 查询任务详情
    response = await client.get(
        f"/api/v1/tasks/{task.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试任务详情"
    assert data["description"] == "详细描述"


@pytest.mark.asyncio
async def test_update_task_as_owner(client: AsyncClient, session: AsyncSession) -> None:
    """测试 PM 更新自己的任务"""
    # 创建 PM 用户
    pm = await create_test_pm(session)

    # 创建任务
    task = Task(
        name="待更新的任务",
        description="原始描述",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    # 更新任务
    response = await client.put(
        f"/api/v1/tasks/{task.id}",
        json={
            "name": "更新后的任务",
            "description": "新描述",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新后的任务"
    assert data["description"] == "新描述"


@pytest.mark.asyncio
async def test_update_task_with_wrong_status_fails(client: AsyncClient, session: AsyncSession) -> None:
    """测试无法更新非 unconfirmed 状态的任务"""
    # 创建 PM 用户
    pm = await create_test_pm(session)

    # 创建已发布的任务
    task = Task(
        name="已发布任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.BIDDING,
        pm_id=pm.id,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    # 尝试更新任务
    response = await client.put(
        f"/api/v1/tasks/{task.id}",
        json={"name": "尝试更新"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # 应该失败，因为任务状态不是 unconfirmed
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, session: AsyncSession) -> None:
    """测试删除任务"""
    # 创建管理员用户
    admin = await create_test_admin(session)

    # 创建 PM 用户
    pm = await create_test_pm(session)

    # 创建任务
    task = Task(
        name="待删除的任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    # 删除任务
    response = await client.delete(
        f"/api/v1/tasks/{task.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    # 验证任务已删除
    response = await client.get(
        f"/api/v1/tasks/{task.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404