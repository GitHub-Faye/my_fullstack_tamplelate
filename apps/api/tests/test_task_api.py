"""
Task API 集成测试

测试 PM 任务管理的核心功能：创建、查询、更新、删除
"""

import uuid
from datetime import datetime, timezone, timedelta as dt_timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Task, TaskStatus, TaskType, User, UserRoleType
from app.core.security import get_password_hash
from tests.conftest import client as async_client_fixture


# ==================== 测试数据准备 ====================

async def create_test_pm(session: AsyncSession) -> User:
    """创建测试 PM 用户（含角色和权限）"""
    from app.core.models import Role, RoleScope, UserRole
    from app.core.scopes import TaskScope, ReportScope, ClientResourceScope, SalaryScope

    pm = User(
        email=f"pm_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test PM",
        role=UserRoleType.PM,
        is_active=True,
    )
    session.add(pm)
    await session.commit()

    # 创建 PM 角色并关联 scopes
    role = Role(name=f"pm_{uuid.uuid4()}")
    session.add(role)
    await session.commit()

    # 关联用户与角色
    user_role = UserRole(user_id=pm.id, role_id=role.id)
    session.add(user_role)

    # 分配 scopes
    for scope in [
        TaskScope.READ, TaskScope.CREATE, TaskScope.UPDATE,
        ReportScope.READ,
        ClientResourceScope.READ, ClientResourceScope.CREATE,
        SalaryScope.READ,
    ]:
        rs = RoleScope(scope=scope.value, role_id=role.id)
        session.add(rs)

    await session.commit()
    return pm


async def create_test_admin(session: AsyncSession) -> User:
    """创建测试管理员用户（含角色和权限）"""
    from app.core.models import Role, RoleScope, UserRole
    from app.core.scopes import TaskScope, ReportScope, BidScope, StarPointScope, SalaryScope, ClientResourceScope, UserScope, RuleScope

    admin = User(
        email=f"admin_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Admin",
        role=UserRoleType.ADMIN,
        is_active=True,
    )
    session.add(admin)
    await session.commit()

    # 创建管理员角色并关联 scopes
    role = Role(name=f"admin_role_{uuid.uuid4()}")
    session.add(role)
    await session.commit()

    user_role = UserRole(user_id=admin.id, role_id=role.id)
    session.add(user_role)

    for scope in [
        TaskScope.READ, TaskScope.CREATE, TaskScope.UPDATE,
        TaskScope.DELETE, TaskScope.ADMIN, TaskScope.APPROVE,
        TaskScope.CONVERT, TaskScope.REASSIGN,
        BidScope.READ,
        ReportScope.READ, ReportScope.ADMIN,
        StarPointScope.READ, StarPointScope.ADMIN,
        SalaryScope.READ, SalaryScope.ADMIN,
        ClientResourceScope.READ,
        UserScope.READ, UserScope.CREATE, UserScope.UPDATE,
        UserScope.DELETE, UserScope.ADMIN,
        RuleScope.ADMIN,
    ]:
        rs = RoleScope(scope=scope.value, role_id=role.id)
        session.add(rs)

    await session.commit()
    return admin


async def create_test_engineer(session: AsyncSession) -> User:
    """创建测试工程师用户（含角色和权限）"""
    from app.core.models import Role, RoleScope, UserRole
    from app.core.scopes import TaskScope, BidScope, ReportScope, StarPointScope, SalaryScope

    engineer = User(
        email=f"engineer_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Engineer",
        role=UserRoleType.ENGINEER,
        is_active=True,
    )
    session.add(engineer)
    await session.commit()

    # 创建工程师角色并关联 scopes
    role = Role(name=f"engineer_{uuid.uuid4()}")
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
    ]:
        rs = RoleScope(scope=scope.value, role_id=role.id)
        session.add(rs)

    await session.commit()
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
        "/v1/tasks/",
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
async def test_create_task_as_engineer_fails(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试工程师无法创建任务"""
    # 创建工程师用户
    engineer = await create_test_engineer(db_session)

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(engineer.id),
        expires_delta=timedelta(minutes=30),
    )

    # 尝试创建任务
    response = await client.post(
        "/v1/tasks/",
        json={
            "name": "测试任务",
            "description": "这是一个测试任务",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # 工程师不应该有 task:create 权限
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_read_tasks_as_pm(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试 PM 查看自己的任务列表"""
    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 创建任务
    task = Task(
        name="PM 的任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    db_session.add(task)
    await db_session.commit()

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    # 查询任务列表
    response = await client.get(
        "/v1/tasks/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["name"] == "PM 的任务"
    assert data["data"][0]["pm_id"] == str(pm.id)


@pytest.mark.asyncio
async def test_read_task_by_id(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试查看任务详情"""
    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 创建任务
    task = Task(
        name="测试任务详情",
        description="详细描述",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    # 查询任务详情
    response = await client.get(
        f"/v1/tasks/{task.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试任务详情"
    assert data["description"] == "详细描述"


@pytest.mark.asyncio
async def test_update_task_as_owner(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试 PM 更新自己的任务"""
    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 创建任务
    task = Task(
        name="待更新的任务",
        description="原始描述",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    # 更新任务
    response = await client.put(
        f"/v1/tasks/{task.id}",
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
async def test_update_task_with_wrong_status_fails(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试无法更新非 unconfirmed 或非 bidding 状态的任务"""
    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 创建进行中的任务（不可编辑状态）
    task = Task(
        name="进行中任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.IN_PROGRESS,
        pm_id=pm.id,
        engineer_id=pm.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    # 尝试更新任务
    response = await client.put(
        f"/v1/tasks/{task.id}",
        json={"name": "尝试更新"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # 应该失败，因为任务状态既不是 unconfirmed 也不是 bidding
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_bidding_task_succeeds(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试可以更新 bidding 状态的任务"""
    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 创建竞价中的任务（可编辑状态）
    task = Task(
        name="竞价中任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.BIDDING,
        pm_id=pm.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    # 尝试更新任务
    response = await client.put(
        f"/v1/tasks/{task.id}",
        json={"name": "更新竞价中任务"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # 应该成功，因为 bidding 状态也可编辑
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新竞价中任务"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试删除任务"""
    # 创建管理员用户
    admin = await create_test_admin(db_session)

    # 创建 PM 用户
    pm = await create_test_pm(db_session)

    # 创建任务
    task = Task(
        name="待删除的任务",
        description="测试任务",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 生成 token
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    # 删除任务
    response = await client.delete(
        f"/v1/tasks/{task.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    # 验证任务已删除
    response = await client.get(
        f"/v1/tasks/{task.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_withdraw_bidding_task(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试 PM 撤回竞价中的任务"""
    pm = await create_test_pm(db_session)

    # 创建竞价中的任务
    task = Task(
        name="竞价中任务",
        description="测试撤回",
        task_type=TaskType.NORMAL,
        status=TaskStatus.BIDDING,
        pm_id=pm.id,
        bidding_deadline=datetime.now(timezone.utc) + dt_timedelta(days=3),
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    # 撤回任务
    response = await client.post(
        f"/v1/tasks/{task.id}/withdraw",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unconfirmed"
    assert data["bidding_deadline"] is None


@pytest.mark.asyncio
async def test_withdraw_non_bidding_task_fails(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试无法撤回非 bidding 状态的任务"""
    pm = await create_test_pm(db_session)

    task = Task(
        name="未确认任务",
        description="测试",
        task_type=TaskType.NORMAL,
        status=TaskStatus.UNCONFIRMED,
        pm_id=pm.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        subject=str(pm.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.post(
        f"/v1/tasks/{task.id}/withdraw",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


# ==================== 筛选参数测试 ====================


@pytest.mark.asyncio
async def test_read_tasks_filter_by_status(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试按状态筛选任务列表"""
    admin = await create_test_admin(db_session)

    # 创建两个不同状态的任务
    pm = await create_test_pm(db_session)
    task1 = Task(name="未确认任务", status=TaskStatus.UNCONFIRMED, pm_id=pm.id, task_type=TaskType.NORMAL)
    task2 = Task(name="进行中任务", status=TaskStatus.IN_PROGRESS, pm_id=pm.id, task_type=TaskType.NORMAL, engineer_id=pm.id)
    db_session.add_all([task1, task2])
    await db_session.commit()

    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(subject=str(admin.id), expires_delta=timedelta(minutes=30))

    # 筛选 unconfirmed
    response = await client.get("/v1/tasks/?status=unconfirmed", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["status"] == "unconfirmed"

    # 不筛选 — 返回全部
    response = await client.get("/v1/tasks/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 2


@pytest.mark.asyncio
async def test_read_tasks_filter_by_task_type(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试按任务类型筛选"""
    admin = await create_test_admin(db_session)
    pm = await create_test_pm(db_session)

    task1 = Task(name="正常任务", task_type=TaskType.NORMAL, status=TaskStatus.UNCONFIRMED, pm_id=pm.id)
    task2 = Task(name="紧急任务", task_type=TaskType.URGENT, status=TaskStatus.UNCONFIRMED, pm_id=pm.id)
    task3 = Task(name="便捷任务", task_type=TaskType.CONVENIENT, status=TaskStatus.UNCONFIRMED, pm_id=pm.id)
    db_session.add_all([task1, task2, task3])
    await db_session.commit()

    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(subject=str(admin.id), expires_delta=timedelta(minutes=30))

    response = await client.get("/v1/tasks/?task_type=urgent", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["task_type"] == "urgent"

    response = await client.get("/v1/tasks/?task_type=convenient", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["task_type"] == "convenient"


@pytest.mark.asyncio
async def test_read_tasks_filter_by_engineer(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试按工程师 ID 筛选"""
    admin = await create_test_admin(db_session)
    pm = await create_test_pm(db_session)
    engineer = await create_test_engineer(db_session)

    task1 = Task(name="工程师的任务", status=TaskStatus.IN_PROGRESS, pm_id=pm.id, engineer_id=engineer.id, task_type=TaskType.NORMAL)
    task2 = Task(name="未分配的任务", status=TaskStatus.UNCONFIRMED, pm_id=pm.id, task_type=TaskType.NORMAL)
    db_session.add_all([task1, task2])
    await db_session.commit()

    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(subject=str(admin.id), expires_delta=timedelta(minutes=30))

    response = await client.get(f"/v1/tasks/?engineer_id={engineer.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["engineer_id"] == str(engineer.id)


@pytest.mark.asyncio
async def test_read_tasks_filter_by_pm_and_exclude(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试按 PM 筛选以及排除指定 PM"""
    admin = await create_test_admin(db_session)
    pm1 = await create_test_pm(db_session)
    pm2 = await create_test_pm(db_session)

    task1 = Task(name="PM1的任务", status=TaskStatus.UNCONFIRMED, pm_id=pm1.id, task_type=TaskType.NORMAL)
    task2 = Task(name="PM2的任务", status=TaskStatus.UNCONFIRMED, pm_id=pm2.id, task_type=TaskType.NORMAL)
    db_session.add_all([task1, task2])
    await db_session.commit()

    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(subject=str(admin.id), expires_delta=timedelta(minutes=30))

    # 筛选 pm1 的任务
    response = await client.get(f"/v1/tasks/?pm_id={pm1.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["pm_id"] == str(pm1.id)

    # 排除 pm1（看其他PM的任务）
    response = await client.get(f"/v1/tasks/?pm_id={pm1.id}&exclude_pm_id=true", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    for t in data["data"]:
        assert t["pm_id"] != str(pm1.id)


# ==================== 多条件组合筛选 ====================


@pytest.mark.asyncio
async def test_read_tasks_combined_filters(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试多条件组合筛选"""
    admin = await create_test_admin(db_session)
    pm = await create_test_pm(db_session)
    engineer = await create_test_engineer(db_session)

    task1 = Task(name="匹配", status=TaskStatus.IN_PROGRESS, task_type=TaskType.URGENT, pm_id=pm.id, engineer_id=engineer.id)
    task2 = Task(name="不匹配-状态", status=TaskStatus.UNCONFIRMED, task_type=TaskType.URGENT, pm_id=pm.id, engineer_id=engineer.id)
    task3 = Task(name="不匹配-类型", status=TaskStatus.IN_PROGRESS, task_type=TaskType.NORMAL, pm_id=pm.id, engineer_id=engineer.id)
    db_session.add_all([task1, task2, task3])
    await db_session.commit()

    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(subject=str(admin.id), expires_delta=timedelta(minutes=30))

    response = await client.get(
        f"/v1/tasks/?status=in_progress&task_type=urgent&engineer_id={engineer.id}&pm_id={pm.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["name"] == "匹配"