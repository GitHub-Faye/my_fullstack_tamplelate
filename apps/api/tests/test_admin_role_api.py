"""
角色管理 API 集成测试

测试管理员角色管理 API：
- 创建角色（含 scopes）
- 获取角色列表
- 获取角色详情
- 更新角色（名称和 scopes）
- 删除角色
- 权限控制
- 操作审计日志
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


async def create_test_regular_user(session: AsyncSession) -> User:
    """创建测试普通用户（无管理权限）"""
    user = User(
        email=f"regular_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Regular User",
        role=UserRoleType.ENGINEER,
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
async def test_admin_create_role(client: AsyncClient, db_session: AsyncSession):
    """测试管理员创建角色"""
    admin = await create_test_admin(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.post(
        "/v1/admin/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "test_role",
            "scopes": ["task:read", "task:create"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_role"
    assert data["scopes"] == ["task:read", "task:create"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_admin_create_role_duplicate_name(client: AsyncClient, db_session: AsyncSession):
    """测试创建同名角色返回错误"""
    admin = await create_test_admin(db_session)

    # 先创建角色
    role = Role(name="duplicate_role")
    db_session.add(role)
    await db_session.commit()

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.post(
        "/v1/admin/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "duplicate_role",
            "scopes": ["task:read"],
        },
    )

    assert response.status_code == 409  # 角色名冲突
    data = response.json()
    assert "already exists" in data["detail"]


@pytest.mark.asyncio
async def test_admin_read_roles(client: AsyncClient, db_session: AsyncSession):
    """测试管理员获取角色列表"""
    admin = await create_test_admin(db_session)

    # 创建几个测试角色
    for i in range(3):
        role = Role(name=f"test_role_{uuid.uuid4().hex[:8]}")
        db_session.add(role)
        await db_session.commit()

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        "/v1/admin/roles",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 3
    assert len(data["data"]) >= 3
    # 验证 scopes 字段存在
    assert "scopes" in data["data"][0]


@pytest.mark.asyncio
async def test_admin_read_role_detail(client: AsyncClient, db_session: AsyncSession):
    """测试管理员获取角色详情"""
    admin = await create_test_admin(db_session)

    # 创建带 scopes 的角色
    role = Role(name="detail_role")
    db_session.add(role)
    await db_session.commit()

    scopes_data = ["task:read", "task:create", "user:read"]
    for scope in scopes_data:
        rs = RoleScope(scope=scope, role_id=role.id)
        db_session.add(rs)
    await db_session.commit()

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        f"/v1/admin/roles/{role.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "detail_role"
    assert len(data["scopes"]) == 3
    assert "task:read" in data["scopes"]
    assert "user:read" in data["scopes"]
    assert data["id"] == str(role.id)


@pytest.mark.asyncio
async def test_admin_read_role_not_found(client: AsyncClient, db_session: AsyncSession):
    """测试获取不存在的角色返回 404"""
    admin = await create_test_admin(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        f"/v1/admin/roles/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_role_name(client: AsyncClient, db_session: AsyncSession):
    """测试管理员更新角色名称"""
    admin = await create_test_admin(db_session)

    role = Role(name="old_name")
    db_session.add(role)
    await db_session.commit()

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.put(
        f"/v1/admin/roles/{role.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "new_name",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "new_name"


@pytest.mark.asyncio
async def test_admin_update_role_scopes(client: AsyncClient, db_session: AsyncSession):
    """测试管理员更新角色 scopes"""
    admin = await create_test_admin(db_session)

    # 创建带旧 scopes 的角色
    role = Role(name="scope_test")
    db_session.add(role)
    await db_session.commit()

    for scope in ["task:read", "task:create"]:
        rs = RoleScope(scope=scope, role_id=role.id)
        db_session.add(rs)
    await db_session.commit()

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    # 替换 scopes
    new_scopes = ["user:read", "user:admin", "task:admin"]
    response = await client.put(
        f"/v1/admin/roles/{role.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "scopes": new_scopes,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["scopes"]) == 3
    assert "user:read" in data["scopes"]
    assert "task:admin" in data["scopes"]
    assert "task:read" not in data["scopes"]  # 旧的被替换了


@pytest.mark.asyncio
async def test_admin_delete_role(client: AsyncClient, db_session: AsyncSession):
    """测试管理员删除角色"""
    admin = await create_test_admin(db_session)

    role = Role(name="to_delete")
    db_session.add(role)
    await db_session.commit()

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.delete(
        f"/v1/admin/roles/{role.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Role deleted successfully"

    # 验证删除
    from sqlalchemy import select as sa_select
    stmt = sa_select(Role).where(Role.id == role.id)
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_admin_delete_role_not_found(client: AsyncClient, db_session: AsyncSession):
    """测试删除不存在的角色返回 404"""
    admin = await create_test_admin(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.delete(
        f"/v1/admin/roles/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_role_api_unauthorized(client: AsyncClient, db_session: AsyncSession):
    """测试普通用户无权访问角色管理 API"""
    user = await create_test_regular_user(db_session)

    token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.get(
        "/v1/admin/roles",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_role_api_unauthenticated(client: AsyncClient, db_session: AsyncSession):
    """测试未登录用户无法访问角色管理 API"""
    response = await client.get("/v1/admin/roles")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_admin_create_role_audit_logged(client: AsyncClient, db_session: AsyncSession):
    """测试创建角色操作自动记录审计日志"""
    admin = await create_test_admin(db_session)

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.post(
        "/v1/admin/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "audit_logged_role",
            "scopes": ["task:read"],
        },
    )

    assert response.status_code == 200
    role_id = response.json()["id"]

    # 验证审计日志
    logs_response = await client.get(
        "/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    logs = logs_response.json()
    assert logs["count"] >= 1
    assert any(
        log["action"] == "role.create" and log["target_id"] == role_id
        for log in logs["data"]
    )


@pytest.mark.asyncio
async def test_admin_update_role_audit_logged(client: AsyncClient, db_session: AsyncSession):
    """测试更新角色操作自动记录审计日志"""
    admin = await create_test_admin(db_session)

    role = Role(name="audit_update")
    db_session.add(role)
    await db_session.commit()

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.put(
        f"/v1/admin/roles/{role.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "audit_updated"},
    )

    assert response.status_code == 200

    # 验证审计日志
    logs_response = await client.get(
        "/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    logs = logs_response.json()
    assert any(
        log["action"] == "role.update" and log["target_id"] == str(role.id)
        for log in logs["data"]
    )


@pytest.mark.asyncio
async def test_admin_delete_role_audit_logged(client: AsyncClient, db_session: AsyncSession):
    """测试删除角色操作自动记录审计日志"""
    admin = await create_test_admin(db_session)

    role = Role(name="audit_delete")
    db_session.add(role)
    await db_session.commit()

    token = create_access_token(
        subject=str(admin.id),
        expires_delta=timedelta(minutes=30),
    )

    response = await client.delete(
        f"/v1/admin/roles/{role.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    # 验证审计日志
    logs_response = await client.get(
        "/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    logs = logs_response.json()
    assert any(
        log["action"] == "role.delete" and log["target_id"] == str(role.id)
        for log in logs["data"]
    )