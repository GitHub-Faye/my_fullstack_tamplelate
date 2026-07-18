"""
管理员用户管理 API 集成测试

测试管理端人员管理 API：
- 创建工程师/PM 账号
- 获取用户列表/详情
- 更新用户信息
- 启用/禁用账号
- 重置密码
- 查看操作日志
- 权限控制
"""

import uuid
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    User,
    UserRoleType,
    Role,
    RoleScope,
    UserRole,
    AuditLog,
)
from app.core.security import get_password_hash, create_access_token
from app.core.scopes import (
    UserScope,
    DashboardScope,
    SalaryScope,
    TaskScope,
    BidScope,
    ReportScope,
    StarPointScope,
    ClientResourceScope,
)


async def create_test_admin(session: AsyncSession) -> User:
    """创建测试管理员用户（含所有管理 scopes）"""
    admin = User(
        email=f"admin_test_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Admin",
        role=UserRoleType.ADMIN,
        is_active=True,
        is_superuser=True,
    )
    session.add(admin)
    await session.commit()

    role = Role(name=f"admin_role_{uuid.uuid4().hex[:8]}")
    session.add(role)
    await session.commit()

    user_role = UserRole(user_id=admin.id, role_id=role.id)
    session.add(user_role)

    for scope in [
        UserScope.READ, UserScope.CREATE, UserScope.UPDATE, UserScope.DELETE, UserScope.ADMIN,
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


async def create_test_regular_user(session: AsyncSession, role_type: UserRoleType = UserRoleType.ENGINEER) -> User:
    """创建测试普通用户（无管理权限）"""
    user = User(
        email=f"regular_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Regular User",
        role=role_type,
        is_active=True,
    )
    session.add(user)
    await session.commit()

    role = Role(name=f"regular_role_{uuid.uuid4().hex[:8]}")
    session.add(role)
    await session.commit()

    user_role = UserRole(user_id=user.id, role_id=role.id)
    session.add(user_role)

    for scope in [
        TaskScope.READ,
        ReportScope.READ,
        SalaryScope.READ,
    ]:
        rs = RoleScope(scope=scope.value, role_id=role.id)
        session.add(rs)

    await session.commit()
    return user


@pytest.mark.asyncio
async def test_admin_create_engineer(client: AsyncClient, db_session: AsyncSession):
    """测试管理员创建工程师账号"""
    admin = await create_test_admin(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.post(
        "/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": f"new_engineer_{uuid.uuid4()}@test.com",
            "password": "testpassword123",
            "full_name": "New Engineer",
            "role": "engineer",
            "S0": 10000.0,
            "H0": 50.0,
            "T_monthly_plan": 160.0,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "engineer"
    assert data["S0"] == 10000.0
    assert data["H0"] == 50.0
    assert data["T_monthly_plan"] == 160.0
    assert data["current_starpoint"] == 0


@pytest.mark.asyncio
async def test_admin_create_pm(client: AsyncClient, db_session: AsyncSession):
    """测试管理员创建 PM 账号"""
    admin = await create_test_admin(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.post(
        "/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": f"new_pm_{uuid.uuid4()}@test.com",
            "password": "testpassword123",
            "full_name": "New PM",
            "role": "pm",
            "S_base": 8000.0,
            "S_assess": 2000.0,
            "R_base": 0.7,
            "R_assess": 0.3,
            "baseline_client_count": 10,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "pm"
    assert data["S_base"] == 8000.0
    assert data["S_assess"] == 2000.0


@pytest.mark.asyncio
async def test_admin_create_user_duplicate_email(client: AsyncClient, db_session: AsyncSession):
    """测试创建重复邮箱用户返回 409"""
    admin = await create_test_admin(db_session)
    email = f"duplicate_{uuid.uuid4()}@test.com"

    # 先创建用户
    existing = User(
        email=email,
        hashed_password=get_password_hash("testpassword"),
        full_name="Existing",
        role=UserRoleType.ENGINEER,
    )
    db_session.add(existing)
    await db_session.commit()

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.post(
        "/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": email,
            "password": "testpassword123",
            "full_name": "Duplicate",
            "role": "engineer",
        },
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_admin_read_users(client: AsyncClient, db_session: AsyncSession):
    """测试管理员获取用户列表"""
    admin = await create_test_admin(db_session)

    # 创建几个测试用户
    for i in range(3):
        user = await create_test_regular_user(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        "/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 4  # admin + 3 regular users
    assert len(data["data"]) >= 4
    assert "S0" in data["data"][0]  # 管理员详情包含工资字段


@pytest.mark.asyncio
async def test_admin_read_user_detail(client: AsyncClient, db_session: AsyncSession):
    """测试管理员获取用户详情"""
    admin = await create_test_admin(db_session)
    engineer = await create_test_regular_user(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        f"/v1/admin/users/{engineer.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(engineer.id)
    assert data["full_name"] == "Regular User"


@pytest.mark.asyncio
async def test_admin_update_user(client: AsyncClient, db_session: AsyncSession):
    """测试管理员更新用户信息"""
    admin = await create_test_admin(db_session)
    engineer = await create_test_regular_user(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.patch(
        f"/v1/admin/users/{engineer.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Updated Name",
            "S0": 15000.0,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["S0"] == 15000.0


@pytest.mark.asyncio
async def test_admin_toggle_user_active(client: AsyncClient, db_session: AsyncSession):
    """测试管理员启用/禁用用户"""
    admin = await create_test_admin(db_session)
    engineer = await create_test_regular_user(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    # 禁用用户
    response = await client.post(
        f"/v1/admin/users/{engineer.id}/toggle-active",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False

    # 验证用户确实被禁用（直接查数据库）
    await db_session.refresh(engineer)
    assert engineer.is_active is False


@pytest.mark.asyncio
async def test_admin_toggle_self_forbidden(client: AsyncClient, db_session: AsyncSession):
    """测试管理员不能禁用自己"""
    admin = await create_test_admin(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.post(
        f"/v1/admin/users/{admin.id}/toggle-active",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_reset_password(client: AsyncClient, db_session: AsyncSession):
    """测试管理员重置用户密码"""
    admin = await create_test_admin(db_session)
    engineer = await create_test_regular_user(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    new_password = "newpassword456"
    response = await client.post(
        f"/v1/admin/users/{engineer.id}/reset-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"new_password": new_password},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully"

    # 验证密码已更新（可以用新密码登录）
    from app.core.security import verify_password
    await db_session.refresh(engineer)
    verified, _ = verify_password(new_password, engineer.hashed_password)
    assert verified is True


@pytest.mark.asyncio
async def test_admin_read_audit_logs(client: AsyncClient, db_session: AsyncSession):
    """测试管理员查看操作日志"""
    admin = await create_test_admin(db_session)
    engineer = await create_test_regular_user(db_session)

    # 直接创建一些审计日志
    for i in range(3):
        log = AuditLog(
            user_id=admin.id,
            action=f"test.action.{i}",
            target_type="user",
            target_id=str(engineer.id),
            details='{"test": true}',
        )
        db_session.add(log)
    await db_session.commit()

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        "/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 3
    assert len(data["data"]) >= 3
    assert data["data"][0]["action"] == "test.action.2"  # 按时间倒序


@pytest.mark.asyncio
async def test_admin_audit_logs_filter_by_type(client: AsyncClient, db_session: AsyncSession):
    """测试操作日志按目标类型筛选"""
    admin = await create_test_admin(db_session)

    log1 = AuditLog(user_id=admin.id, action="user.create", target_type="user", target_id=str(uuid.uuid4()))
    log2 = AuditLog(user_id=admin.id, action="task.create", target_type="task", target_id=str(uuid.uuid4()))
    db_session.add(log1)
    db_session.add(log2)
    await db_session.commit()

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        "/v1/admin/audit-logs?target_type=task",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    for log in data["data"]:
        assert log["target_type"] == "task"


@pytest.mark.asyncio
async def test_admin_api_unauthorized(client: AsyncClient, db_session: AsyncSession):
    """测试普通用户无权访问管理 API"""
    user = await create_test_regular_user(db_session)

    token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=30),
    )

    # 尝试访问管理端点
    response = await client.get(
        "/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_api_unauthenticated(client: AsyncClient, db_session: AsyncSession):
    """测试未登录用户无法访问管理 API"""
    response = await client.get("/v1/admin/users")
    # 未提供令牌时，get_current_user 抛出 401 Unauthorized
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_admin_create_user_audit_logged(client: AsyncClient, db_session: AsyncSession):
    """测试创建用户操作自动记录审计日志"""
    admin = await create_test_admin(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.post(
        "/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": f"audit_logged_{uuid.uuid4()}@test.com",
            "password": "testpassword123",
            "full_name": "Audit Logged",
            "role": "engineer",
        },
    )

    assert response.status_code == 200
    user_id = response.json()["id"]

    # 验证审计日志
    logs_response = await client.get(
        "/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    logs = logs_response.json()
    assert logs["count"] >= 1
    assert any(
        log["action"] == "user.create" and log["target_id"] == user_id
        for log in logs["data"]
    )