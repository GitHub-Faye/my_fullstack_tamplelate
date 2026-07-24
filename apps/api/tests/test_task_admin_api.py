"""
Task Admin API 集成测试

测试管理员任务审核与发布功能：审核通过、发布、类型转换
"""

import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Task, TaskStatus, TaskType, User, UserRoleType
from app.core.security import get_password_hash, create_access_token


# ==================== 测试数据准备 ====================

async def create_test_admin(db_session: AsyncSession) -> User:
    """创建测试管理员用户"""
    admin = User(
        email=f"admin_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Admin",
        role=UserRoleType.ADMIN,
        is_active=True,
        is_superuser=True,  # 添加超管标志
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


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


# ==================== 测试用例：发布任务 ====================

@pytest.mark.asyncio
async def test_publish_task_success(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试管理员发布任务到竞价池"""
    # 创建管理员和 PM 用户
    admin = await create_test_admin(db_session)
    pm = await create_test_pm(db_session)

    # 创建已确认未发布的任务
    task = Task(
        name="待发布任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 生成管理员 token
    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    # 发布任务
    response = await client.post(
        f"/v1/tasks/{task.id}/publish",
        params={"bidding_days": 5},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "bidding"
    assert data["bidding_deadline"] is not None


# ==================== 测试用例：类型转换 ====================

@pytest.mark.asyncio
async def test_convert_to_urgent_success(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试转换为紧急任务"""
    # 创建管理员和 PM 用户
    admin = await create_test_admin(db_session)
    pm = await create_test_pm(db_session)

    # 创建普通任务
    task = Task(
        name="普通任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 生成管理员 token
    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    # 转换为紧急任务
    response = await client.post(
        f"/v1/tasks/{task.id}/convert-urgent",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["task_type"] == "urgent"


@pytest.mark.asyncio
async def test_convert_to_convenient_success(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试转换为便捷任务"""
    # 创建管理员和 PM 用户
    admin = await create_test_admin(db_session)
    pm = await create_test_pm(db_session)

    # 创建普通任务
    task = Task(
        name="普通任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 生成管理员 token
    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    # 转换为便捷任务
    response = await client.post(
        f"/v1/tasks/{task.id}/convert-convenient",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["task_type"] == "convenient"


@pytest.mark.asyncio
async def test_convert_already_urgent_fails(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试已经是紧急任务无法再次转换"""
    # 创建管理员和 PM 用户
    admin = await create_test_admin(db_session)
    pm = await create_test_pm(db_session)

    # 创建紧急任务
    task = Task(
        name="紧急任务",
        description="测试任务",
        task_type=TaskType.URGENT,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 生成管理员 token
    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    # 尝试再次转换为紧急任务
    response = await client.post(
        f"/v1/tasks/{task.id}/convert-urgent",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


