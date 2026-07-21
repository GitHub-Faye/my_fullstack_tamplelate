"""
审计日志模块 — API 集成测试

测试统一审计日志查询端点 /v1/audit-logs 的权限控制、筛选功能和分页。
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import AuditLog, Task, TaskStatus, TaskType, User, UserRoleType
from app.core.security import get_password_hash, create_access_token


async def _create_user_with_role(
    session: AsyncSession,
    role_type: UserRoleType,
    full_name: str,
    scopes: list,
) -> User:
    """创建指定角色的测试用户"""
    from app.core.models import Role, RoleScope, UserRole
    from app.core.scopes import TaskScope, UserScope

    user = User(
        email=f"{role_type.value}_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("test"),
        full_name=full_name,
        role=role_type,
        is_active=True,
    )
    session.add(user)
    await session.commit()

    role = Role(name=f"role_{role_type.value}_{uuid.uuid4()}")
    session.add(role)
    await session.commit()

    session.add(UserRole(user_id=user.id, role_id=role.id))
    for scope in scopes:
        session.add(RoleScope(scope=scope.value, role_id=role.id))
    await session.commit()
    return user


async def create_admin(session: AsyncSession) -> User:
    """创建测试管理员"""
    from app.core.scopes import TaskScope, UserScope
    return await _create_user_with_role(session, UserRoleType.ADMIN, "测试管理员", [TaskScope.ADMIN, UserScope.READ])


async def create_pm(session: AsyncSession) -> User:
    """创建测试市场产品PM"""
    from app.core.scopes import TaskScope
    return await _create_user_with_role(session, UserRoleType.PM, "测试PM", [TaskScope.READ])


async def create_engineer(session: AsyncSession) -> User:
    """创建测试工程师"""
    from app.core.scopes import TaskScope
    return await _create_user_with_role(session, UserRoleType.ENGINEER, "测试工程师", [TaskScope.READ])


@pytest.mark.asyncio
async def test_audit_logs_admin_can_read_all(client: AsyncClient, db_session: AsyncSession):
    """测试管理员可查看所有审计日志"""
    admin = await create_admin(db_session)
    pm = await create_pm(db_session)

    # 创建两个不同用户的日志
    for user_id in [admin.id, pm.id]:
        log = AuditLog(user_id=user_id, action="test.action", target_type="user", target_id=str(uuid.uuid4()))
        db_session.add(log)
    await db_session.commit()

    token = create_access_token(subject=str(admin.id), expires_delta=timedelta(minutes=30))
    response = await client.get("/v1/audit-logs/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 2


@pytest.mark.asyncio
async def test_audit_logs_admin_filter_by_user_id(client: AsyncClient, db_session: AsyncSession):
    """测试管理员可按指定 user_id 筛选"""
    admin = await create_admin(db_session)
    pm = await create_pm(db_session)

    db_session.add(AuditLog(user_id=admin.id, action="admin.action", target_type="user", target_id=str(uuid.uuid4())))
    db_session.add(AuditLog(user_id=pm.id, action="pm.action", target_type="task", target_id=str(uuid.uuid4())))
    await db_session.commit()

    token = create_access_token(subject=str(admin.id), expires_delta=timedelta(minutes=30))

    # 管理员按 pm 的 user_id 筛选
    response = await client.get(f"/v1/audit-logs/?user_id={pm.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    for log in data["data"]:
        assert log["user_id"] == str(pm.id)


@pytest.mark.asyncio
async def test_audit_logs_pm_can_only_read_own(client: AsyncClient, db_session: AsyncSession):
    """测试市场产品PM 只能查看自己的操作日志"""
    admin = await create_admin(db_session)
    pm = await create_pm(db_session)

    # 创建 admin 和 pm 的日志
    db_session.add(AuditLog(user_id=admin.id, action="admin.action", target_type="user", target_id=str(uuid.uuid4())))
    db_session.add(AuditLog(user_id=pm.id, action="pm.action", target_type="task", target_id=str(uuid.uuid4())))
    await db_session.commit()

    token = create_access_token(subject=str(pm.id), expires_delta=timedelta(minutes=30))
    response = await client.get("/v1/audit-logs/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    # PM 应只看到自己的日志
    for log in data["data"]:
        assert log["user_id"] == str(pm.id)


@pytest.mark.asyncio
async def test_audit_logs_engineer_can_only_read_own(client: AsyncClient, db_session: AsyncSession):
    """测试工程师只能查看自己的操作日志"""
    admin = await create_admin(db_session)
    eng = await create_engineer(db_session)

    db_session.add(AuditLog(user_id=eng.id, action="eng.action", target_type="task", target_id=str(uuid.uuid4())))
    db_session.add(AuditLog(user_id=admin.id, action="admin.action", target_type="user", target_id=str(uuid.uuid4())))
    await db_session.commit()

    token = create_access_token(subject=str(eng.id), expires_delta=timedelta(minutes=30))
    response = await client.get("/v1/audit-logs/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    for log in data["data"]:
        assert log["user_id"] == str(eng.id)


@pytest.mark.asyncio
async def test_audit_logs_filter_by_action(client: AsyncClient, db_session: AsyncSession):
    """测试按操作类型筛选"""
    admin = await create_admin(db_session)

    db_session.add(AuditLog(user_id=admin.id, action="task.create", target_type="task", target_id=str(uuid.uuid4())))
    db_session.add(AuditLog(user_id=admin.id, action="user.create", target_type="user", target_id=str(uuid.uuid4())))
    await db_session.commit()

    token = create_access_token(subject=str(admin.id), expires_delta=timedelta(minutes=30))
    response = await client.get("/v1/audit-logs/?action=task.create", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    for log in data["data"]:
        assert log["action"] == "task.create"


@pytest.mark.asyncio
async def test_audit_logs_filter_by_target_type(client: AsyncClient, db_session: AsyncSession):
    """测试按目标类型筛选"""
    admin = await create_admin(db_session)

    db_session.add(AuditLog(user_id=admin.id, action="test", target_type="task", target_id=str(uuid.uuid4())))
    db_session.add(AuditLog(user_id=admin.id, action="test", target_type="user", target_id=str(uuid.uuid4())))
    await db_session.commit()

    token = create_access_token(subject=str(admin.id), expires_delta=timedelta(minutes=30))
    response = await client.get("/v1/audit-logs/?target_type=task", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    for log in data["data"]:
        assert log["target_type"] == "task"


@pytest.mark.asyncio
async def test_audit_logs_pagination(client: AsyncClient, db_session: AsyncSession):
    """测试分页功能"""
    admin = await create_admin(db_session)

    for i in range(5):
        db_session.add(AuditLog(user_id=admin.id, action=f"test.{i}", target_type="user", target_id=str(uuid.uuid4())))
    await db_session.commit()

    token = create_access_token(subject=str(admin.id), expires_delta=timedelta(minutes=30))

    # 第1页，每页2条
    response = await client.get("/v1/audit-logs/?page=1&page_size=2", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["total_pages"] >= 3

    # 第3页
    response = await client.get("/v1/audit-logs/?page=3&page_size=2", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_audit_logs_operator_name_filled(client: AsyncClient, db_session: AsyncSession):
    """测试 user_name 字段正确填充"""
    admin = await create_admin(db_session)

    log = AuditLog(user_id=admin.id, action="test", target_type="user", target_id=str(uuid.uuid4()))
    db_session.add(log)
    await db_session.commit()

    token = create_access_token(subject=str(admin.id), expires_delta=timedelta(minutes=30))
    response = await client.get("/v1/audit-logs/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    log_data = next(l for l in data["data"] if l["action"] == "test")
    assert log_data["operator_name"] == "测试管理员"


@pytest.mark.asyncio
async def test_audit_logs_unauthorized(client: AsyncClient, db_session: AsyncSession):
    """测试未登录用户无法访问"""
    response = await client.get("/v1/audit-logs/")
    assert response.status_code == 401
