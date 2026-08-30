"""
Tests for role management endpoints.

Tests cover:
- Role CRUD operations
- Scope management (validation, replace on update)
- Permission checks (scope-based, not superuser-based)
- Pagination
- Built-in role protection
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.models import User, Role, RoleScope, UserRole
from app.core.scopes import DEFAULT_ROLE_SCOPES, ALL_SCOPES


def _admin_headers(user_token: str) -> dict[str, str]:
    """构造带 Authorization 头的请求头"""
    return {"Authorization": f"Bearer {user_token}"}


# ======================== 获取角色列表测试 ========================

@pytest.mark.asyncio
async def test_read_roles_viewer_forbidden(
    authorized_client: AsyncClient,
):
    """
    测试仅有 user:read scope 的用户（viewer 角色）不能读取角色列表（403）。

    角色管理使用专属 role:read scope，viewer（只有 user:read）无权访问。
    """
    response = await authorized_client.get("/v1/roles/")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_read_roles_role_admin(
    role_admin_client: AsyncClient,
):
    """
    测试拥有 role:read scope 的用户（role_manager）可以获取角色列表。
    role_manager scopes: role:read, role:create, role:update, role:delete
    """
    response = await role_admin_client.get("/v1/roles/")

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] >= 3  # viewer / editor / admin 三个预置角色
    # 每个角色都带有 scopes 字段
    for role in data["data"]:
        assert "scopes" in role
        assert isinstance(role["scopes"], list)


@pytest.mark.asyncio
async def test_read_roles_unauthorized(client: AsyncClient):
    """
    测试未登录用户无法获取角色列表。
    """
    response = await client.get("/v1/roles/")

    assert response.status_code in [401, 403]  # OAuth2 返回 401 for missing token


# ======================== 获取单个角色测试 ========================

@pytest.mark.asyncio
async def test_read_role_by_id(
    role_admin_client: AsyncClient,
    db_session: AsyncSession,
):
    """
    测试获取单个角色详情（含 scopes）。
    """
    # 查询预置的 admin 角色
    stmt = select(Role).where(Role.name == "admin")
    role = (await db_session.execute(stmt)).scalar_one()

    response = await role_admin_client.get(f"/v1/roles/{role.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "admin"
    assert "user:read" in data["scopes"]
    assert "role:read" in data["scopes"]


@pytest.mark.asyncio
async def test_read_role_not_found(role_admin_client: AsyncClient):
    """
    测试获取不存在的角色返回 404。
    """
    fake_id = uuid.uuid4()
    response = await role_admin_client.get(f"/v1/roles/{fake_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# ======================== 创建角色测试 ========================

@pytest.mark.asyncio
async def test_create_role_success(
    role_admin_client: AsyncClient,
    db_session: AsyncSession,
):
    """
    测试成功创建角色（带 scopes）。

    role_manager 用户拥有 role:create scope，因此可以创建角色。
    """
    response = await role_admin_client.post(
        "/v1/roles/",
        json={
            "name": "operator",
            "scopes": ["user:read", "user:create"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "operator"
    # scopes 响应为稳定排序（repository 内 sorted）
    assert set(data["scopes"]) == {"user:read", "user:create"}

    # 数据库中确实存在
    stmt = select(Role).where(Role.name == "operator")
    role = (await db_session.execute(stmt)).scalar_one()
    assert role is not None


@pytest.mark.asyncio
async def test_create_role_duplicate_name(role_admin_client: AsyncClient):
    """
    测试创建重名角色返回 400。
    """
    response = await role_admin_client.post(
        "/v1/roles/",
        json={
            "name": "editor",  # 预置角色名
            "scopes": ["user:read"],
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_role_invalid_scope(role_admin_client: AsyncClient):
    """
    测试创建角色时传入未定义的 scope 返回 400。
    """
    response = await role_admin_client.post(
        "/v1/roles/",
        json={
            "name": "evil",
            "scopes": ["user:read", "order:admin"],  # order:admin 不存在
        },
    )

    assert response.status_code == 400
    assert "Unknown scopes" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_role_validation_error(role_admin_client: AsyncClient):
    """
    测试创建角色时缺少必填字段（name）返回 422。
    """
    response = await role_admin_client.post(
        "/v1/roles/",
        json={"scopes": ["user:read"]},
    )

    assert response.status_code == 422


# ======================== 更新角色测试 ========================

@pytest.mark.asyncio
async def test_update_role_name_only(role_admin_client: AsyncClient):
    """
    测试只更新角色名（scopes 保持不变）。
    """
    response = await role_admin_client.post(
        "/v1/roles/",
        json={"name": "temp_role", "scopes": ["user:read"]},
    )
    role_id = response.json()["id"]

    # 只改名字
    response = await role_admin_client.patch(
        f"/v1/roles/{role_id}",
        json={"name": "renamed_role"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "renamed_role"
    # scopes 应保持不变（响应为排序后的稳定顺序）
    assert set(data["scopes"]) == {"user:read"}


@pytest.mark.asyncio
async def test_update_role_scopes_replace(role_admin_client: AsyncClient):
    """
    测试更新角色 scopes：整体替换（增删 scope）。
    """
    # 创建带 2 个 scope 的角色
    response = await role_admin_client.post(
        "/v1/roles/",
        json={"name": "scoped_role", "scopes": ["user:read", "user:create"]},
    )
    role_id = response.json()["id"]

    # 整体替换为另外 2 个 scope
    response = await role_admin_client.patch(
        f"/v1/roles/{role_id}",
        json={"scopes": ["user:update", "user:delete"]},
    )

    assert response.status_code == 200
    data = response.json()
    # scopes 整体替换
    assert set(data["scopes"]) == {"user:update", "user:delete"}

    # 再清空 scopes
    response = await role_admin_client.patch(
        f"/v1/roles/{role_id}",
        json={"scopes": []},
    )

    assert response.status_code == 200
    assert response.json()["scopes"] == []


@pytest.mark.asyncio
async def test_update_role_name_and_scopes_together(role_admin_client: AsyncClient):
    """
    测试同时修改角色名和 scopes（核心需求：改名字 + 改它持有的 scope）。
    """
    # 创建角色
    response = await role_admin_client.post(
        "/v1/roles/",
        json={"name": "old_name", "scopes": ["user:read"]},
    )
    role_id = response.json()["id"]

    # 同时修改名字 + scopes
    response = await role_admin_client.patch(
        f"/v1/roles/{role_id}",
        json={
            "name": "new_name",
            "scopes": ["user:read", "user:create", "role:read"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "new_name"
    assert set(data["scopes"]) == {"user:read", "user:create", "role:read"}


@pytest.mark.asyncio
async def test_update_role_not_found(role_admin_client: AsyncClient):
    """
    测试更新不存在的角色返回 404。
    """
    fake_id = uuid.uuid4()
    response = await role_admin_client.patch(
        f"/v1/roles/{fake_id}",
        json={"name": "nobody"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_builtin_role_forbidden(role_admin_client: AsyncClient):
    """
    测试修改预置角色（viewer/editor/admin）返回 400。
    """
    # 查询预置的 admin 角色
    response = await role_admin_client.get("/v1/roles/")
    roles = response.json()["data"]
    admin_role = next(r for r in roles if r["name"] == "admin")

    response = await role_admin_client.patch(
        f"/v1/roles/{admin_role['id']}",
        json={"name": "hacked_admin"},
    )

    assert response.status_code == 400
    assert "cannot be modified" in response.json()["detail"]


# ======================== 删除角色测试 ========================

@pytest.mark.asyncio
async def test_delete_role_success(
    role_admin_client: AsyncClient,
    db_session: AsyncSession,
):
    """
    测试成功删除自定义角色。

    role_manager 用户拥有 role:delete scope。
    """
    # 创建角色
    response = await role_admin_client.post(
        "/v1/roles/",
        json={"name": "disposable", "scopes": ["user:read"]},
    )
    role_id = response.json()["id"]

    # 删除
    response = await role_admin_client.delete(f"/v1/roles/{role_id}")

    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]

    # 数据库中已不存在
    response = await role_admin_client.get(f"/v1/roles/{role_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_role_not_found(role_admin_client: AsyncClient):
    """
    测试删除不存在的角色返回 404。
    """
    fake_id = uuid.uuid4()
    response = await role_admin_client.delete(f"/v1/roles/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_builtin_role_forbidden(role_admin_client: AsyncClient):
    """
    测试删除预置角色返回 400。
    """
    response = await role_admin_client.get("/v1/roles/")
    roles = response.json()["data"]
    viewer_role = next(r for r in roles if r["name"] == "viewer")

    response = await role_admin_client.delete(f"/v1/roles/{viewer_role['id']}")

    assert response.status_code == 400
    assert "cannot be deleted" in response.json()["detail"]


# ======================== 权限（scope）控制测试 ========================

@pytest.mark.asyncio
async def test_user_without_role_scope_cannot_delete(
    client: AsyncClient,
    test_superuser: User,
    superuser_token: str,
    db_session: AsyncSession,
):
    """
    测试没有 role:* scope 的用户（editor）不能删除角色（403）。

    构造一个只有 user 读/写 scope 的 editor 用户，验证角色删除需要专属 role:delete scope。
    """
    # 创建只有 user scope 的用户（默认 editor 角色，无 role:* scope）
    editor_role = (await db_session.execute(
        select(Role).where(Role.name == "editor")
    )).scalar_one()

    limited_user = User(
        email="limited@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(limited_user)
    await db_session.flush()
    db_session.add(UserRole(user_id=limited_user.id, role_id=editor_role.id))
    await db_session.commit()

    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(subject=str(limited_user.id), expires_delta=timedelta(minutes=30))
    headers = _admin_headers(token)

    # 先由超管创建角色
    admin_headers = _admin_headers(superuser_token)
    create_resp = await client.post(
        "/v1/roles/",
        json={"name": "grp", "scopes": ["user:read"]},
        headers=admin_headers,
    )
    role_id = create_resp.json()["id"]

    # editor 用户删除角色应返回 403（没有 role:delete）
    response = await client.delete(f"/v1/roles/{role_id}", headers=headers)
    assert response.status_code == 403

    # 也无法读取角色列表（没有 role:read）
    response = await client.get("/v1/roles/", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_superuser_has_all_scopes(
    superuser_client: AsyncClient,
):
    """
    测试超管拥有全部 scope，可以访问所有角色端点（is_superuser 无需显式判断）。
    """
    response = await superuser_client.get("/v1/roles/")
    assert response.status_code == 200

    response = await superuser_client.post(
        "/v1/roles/",
        json={"name": "su_role", "scopes": ["role:read"]},
    )
    assert response.status_code == 200


# ======================== 分页测试 ========================

@pytest.mark.asyncio
async def test_read_roles_pagination(
    role_admin_client: AsyncClient,
):
    """
    测试角色列表分页功能。
    """
    response = await role_admin_client.get("/v1/roles/?page=1&page_size=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2
