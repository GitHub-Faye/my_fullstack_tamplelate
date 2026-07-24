"""
简化的 Task API 单元测试

直接测试 repository 和 schemas，不依赖完整的 API
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Task, TaskStatus, TaskType, User, UserRoleType
from app.core.security import get_password_hash
from app.domains.task.repository import (
    create_task,
    get_task,
    get_tasks,
    update_task,
    delete_task,
)
from app.domains.task.schemas import TaskCreate, TaskUpdate


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


# ==================== Repository 测试 ====================

@pytest.mark.asyncio
async def test_create_task_repository(db_session: AsyncSession) -> None:
    """测试创建任务"""
    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 创建任务
    task_create = TaskCreate(
        name="测试任务",
        description="这是一个测试任务",
        task_type=TaskType.NORMAL,
    )

    task = await create_task(
        session=db_session,
        task_in=task_create,
        pm_id=pm.id,
    )

    assert task.id is not None
    assert task.name == "测试任务"
    assert task.status == TaskStatus.UNCONFIRMED
    assert task.pm_id == pm.id
    assert task.task_type == TaskType.NORMAL


@pytest.mark.asyncio
async def test_get_task_repository(db_session: AsyncSession) -> None:
    """测试获取任务"""
    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 创建任务
    task_create = TaskCreate(
        name="测试任务",
        description="测试描述",
    )

    created_task = await create_task(
        session=db_session,
        task_in=task_create,
        pm_id=pm.id,
    )

    # 获取任务
    task = await get_task(session=db_session, task_id=created_task.id)

    assert task is not None
    assert task.id == created_task.id
    assert task.name == "测试任务"


@pytest.mark.asyncio
async def test_get_tasks_repository(db_session: AsyncSession) -> None:
    """测试获取任务列表"""
    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 创建多个任务
    for i in range(3):
        task_create = TaskCreate(
            name=f"任务 {i+1}",
            description=f"描述 {i+1}",
        )
        await create_task(
            session=db_session,
            task_in=task_create,
            pm_id=pm.id,
        )

    # 获取任务列表
    tasks, count = await get_tasks(
        session=db_session,
        pm_id=pm.id,
        skip=0,
        limit=10,
    )

    assert count == 3
    assert len(tasks) == 3
    assert tasks[0].pm_id == pm.id


@pytest.mark.asyncio
async def test_update_task_repository(db_session: AsyncSession) -> None:
    """测试更新任务"""
    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 创建任务
    task_create = TaskCreate(
        name="原始任务名",
        description="原始描述",
    )

    created_task = await create_task(
        session=db_session,
        task_in=task_create,
        pm_id=pm.id,
    )

    # 更新任务
    task_update = TaskUpdate(
        name="更新后的任务名",
        description="更新后的描述",
    )

    updated_task = await update_task(
        session=db_session,
        db_task=created_task,
        task_in=task_update,
    )

    assert updated_task.name == "更新后的任务名"
    assert updated_task.description == "更新后的描述"


@pytest.mark.asyncio
async def test_delete_task_repository(db_session: AsyncSession) -> None:
    """测试删除任务"""
    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 创建任务
    task_create = TaskCreate(
        name="待删除的任务",
        description="将被删除",
    )

    created_task = await create_task(
        session=db_session,
        task_in=task_create,
        pm_id=pm.id,
    )

    # 删除任务
    await delete_task(session=db_session, db_task=created_task)

    # 验证任务已删除
    task = await get_task(session=db_session, task_id=created_task.id)
    assert task is None


@pytest.mark.asyncio
async def test_task_status_filter(db_session: AsyncSession) -> None:
    """测试按状态过滤任务"""
    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 创建不同状态的任务
    task1 = await create_task(
        session=db_session,
        task_in=TaskCreate(name="未确认任务"),
        pm_id=pm.id,
    )

    task2 = Task(
        name="已发布任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.BIDDING,
        pm_id=pm.id,
    )
    db_session.add(task2)
    await db_session.commit()

    # 按状态过滤
    unconfirmed_tasks, count = await get_tasks(
        session=db_session,
        pm_id=pm.id,
        status=TaskStatus.UNCONFIRMED,
        skip=0,
        limit=10,
    )

    assert count == 1
    assert unconfirmed_tasks[0].status == TaskStatus.UNCONFIRMED


# ==================== Schema 测试 ====================

def test_task_create_schema() -> None:
    """测试 TaskCreate schema"""
    task_create = TaskCreate(
        name="测试任务",
        description="描述",
        task_type=TaskType.URGENT,
    )

    assert task_create.name == "测试任务"
    assert task_create.task_type == TaskType.URGENT


def test_task_update_schema() -> None:
    """测试 TaskUpdate schema"""
    task_update = TaskUpdate(
        name="更新名称",
        description=None,
    )

    assert task_update.name == "更新名称"
    assert task_update.description is None


def test_task_public_schema() -> None:
    """测试 TaskPublic schema"""
    from app.domains.task.schemas import TaskPublic

    task_id = uuid.uuid4()
    pm_id = uuid.uuid4()

    task_public = TaskPublic(
        id=task_id,
        name="测试任务",
        description="描述",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm_id,
        pm_name="Test PM",
    )

    assert task_public.id == task_id
    assert task_public.pm_id == pm_id
    assert task_public.pm_name == "Test PM"
    assert task_public.status == TaskStatus.UNCONFIRMED