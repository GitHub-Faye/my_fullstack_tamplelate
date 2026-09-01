"""
Tests for user management endpoints.

Tests cover:
- User registration (signup)
- User CRUD operations (superuser only)
- Current user operations (me endpoints)
- User update and delete
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Role, RoleScopeModel, User, UserRole
from app.core.security import get_password_hash

# ======================== 响应字段安全断言（P0-1） ========================
# 所有返回 User 数据的端点都不得泄露 hashed_password。
# 该断言是输出加固的守护：任何新增/改造端点若破坏 UserPublic 过滤，
# 此处会立即失败。

SCHEMA_FIELDS_TO_REDACT = {"hashed_password", "password"}


def assert_no_password_fields(data: dict) -> None:
    """断言响应对象不包含任何敏感字段。"""
    assert "hashed_password" not in data, "响应泄露 hashed_password"
    # password 仅用于请求模型，响应中出现即异常
    assert "password" not in data, "响应泄露 password"


@pytest.mark.asyncio
async def test_user_responses_never_leak_password(
    superuser_client: AsyncClient,
    test_user: User,
    test_superuser: User,
    db_session: AsyncSession,
):
    """
    覆盖所有返回用户数据的端点，断言均不泄露 hashed_password/password。

    防回归用例：若某端点误将 DB 模型（User）直接返回，此测试失败。
    """
    # 1. 当前用户
    resp = await superuser_client.get("/v1/users/me")
    assert resp.status_code == 200
    assert_no_password_fields(resp.json())

    # 2. 用户列表（逐项检查）
    resp = await superuser_client.get("/v1/users/")
    assert resp.status_code == 200
    for item in resp.json()["data"]:
        assert_no_password_fields(item)

    # 3. 单个用户（他人）
    resp = await superuser_client.get(f"/v1/users/{test_user.id}")
    assert resp.status_code == 200
    assert_no_password_fields(resp.json())

    # 4. 创建用户
    resp = await superuser_client.post(
        "/v1/users/",
        json={
            "email": "guard@example.com",
            "password": "guardpass123",
            "full_name": "Guard User",
        },
    )
    assert resp.status_code == 200
    assert_no_password_fields(resp.json())

    # 5. 更新用户
    resp = await superuser_client.patch(
        f"/v1/users/{test_user.id}",
        json={"full_name": "Guarded"},
    )
    assert resp.status_code == 200
    assert_no_password_fields(resp.json())

    # 6. 更新当前用户
    resp = await superuser_client.patch("/v1/users/me", json={"full_name": "Guard Me"})
    assert resp.status_code == 200
    assert_no_password_fields(resp.json())

    # 7. 登录令牌（不含用户对象，仍应无敏感字段）
    resp = await superuser_client.post(
        "/v1/login/access-token",
        data={
            "username": test_superuser.email,
            "password": "adminpassword123",
            "grant_type": "password",
        },
    )
    assert resp.status_code == 200
    assert_no_password_fields(resp.json())


# ======================== 用户注册测试 ========================

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """
    测试用户自助注册成功。
    """
    response = await client.post(
        "/v1/users/signup",
        json={
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_user_duplicate_email(client: AsyncClient, test_user: User):
    """
    测试使用已存在的邮箱注册失败。
    """
    response = await client.post(
        "/v1/users/signup",
        json={
            "email": test_user.email,  # 已存在的邮箱
            "password": "password123",
            "full_name": "Another User",
        },
    )
    
    # 邮箱唯一性冲突返回 409（与 USER_EMAIL_ALREADY_EXISTS → 409 的约定一致）
    assert response.status_code == 409
    data = response.json()
    assert "already exists" in data["detail"]


@pytest.mark.asyncio
async def test_register_user_invalid_email(client: AsyncClient):
    """
    测试使用无效的邮箱格式注册失败。
    """
    response = await client.post(
        "/v1/users/signup",
        json={
            "email": "invalid-email",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_validation_error_protocol_shape(client: AsyncClient):
    """
    测试 422 校验错误与 BusinessException 同构：{detail, code, data.errors}。

    守护 P0-2 约定：SDK/前端可按统一 ErrorResponse 消费所有错误。
    """
    response = await client.post(
        "/v1/users/signup",
        json={
            "email": "invalid-email",
            "password": "password123",
        },
    )

    assert response.status_code == 422
    body = response.json()
    # 统一错误协议：detail（字符串）+ code（错误码）+ data（结构化明细）
    assert body["code"] == "SYSTEM_VALIDATION_ERROR"
    assert isinstance(body["detail"], str)
    assert "errors" in body["data"]
    assert isinstance(body["data"]["errors"], list)


@pytest.mark.asyncio
async def test_register_user_short_password(client: AsyncClient):
    """
    测试使用太短的密码注册失败。
    """
    response = await client.post(
        "/v1/users/signup",
        json={
            "email": "test@example.com",
            "password": "short",  # 少于8位
            "full_name": "Test User",
        },
    )
    
    assert response.status_code == 422  # Validation error


# ======================== 获取当前用户信息测试 ========================

@pytest.mark.asyncio
async def test_read_user_me(authorized_client: AsyncClient, test_user: User):
    """
    测试获取当前登录用户的信息。
    """
    response = await authorized_client.get("/v1/users/me")
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    assert data["id"] == str(test_user.id)
    assert data["is_active"] == test_user.is_active


@pytest.mark.asyncio
async def test_read_user_me_unauthorized(client: AsyncClient):
    """
    测试未登录用户无法获取用户信息。
    """
    response = await client.get("/v1/users/me")
    
    assert response.status_code in [401, 403]  # OAuth2 returns 401 for missing token


# ======================== 更新当前用户信息测试 ========================

@pytest.mark.asyncio
async def test_update_user_me(authorized_client: AsyncClient, test_user: User):
    """
    测试更新当前用户自己的信息。
    """
    response = await authorized_client.patch(
        "/v1/users/me",
        json={
            "full_name": "Updated Name",
            "email": "updated@example.com",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == "updated@example.com"


@pytest.mark.asyncio
async def test_update_user_me_duplicate_email(
    authorized_client: AsyncClient, 
    test_user: User,
    db_session: AsyncSession
):
    """
    测试更新邮箱为已被其他用户使用的邮箱失败。
    """
    # 创建另一个用户
    other_user = User(
        email="other@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Other User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(other_user)
    await db_session.commit()
    
    response = await authorized_client.patch(
        "/v1/users/me",
        json={
            "email": "other@example.com",  # 已被其他用户使用
        },
    )
    
    assert response.status_code == 409
    data = response.json()
    assert "already exists" in data["detail"]


# ======================== 修改密码测试 ========================

@pytest.mark.asyncio
async def test_update_password_me_success(authorized_client: AsyncClient, test_user: User):
    """
    测试成功修改当前用户密码。
    """
    response = await authorized_client.patch(
        "/v1/users/me/password",
        json={
            "current_password": "testpassword123",
            "new_password": "newpassword456",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "Password updated successfully" in data["message"]


@pytest.mark.asyncio
async def test_update_password_me_wrong_current(authorized_client: AsyncClient):
    """
    测试使用错误的当前密码修改密码失败。
    """
    response = await authorized_client.patch(
        "/v1/users/me/password",
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
        },
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Incorrect password" in data["detail"]


@pytest.mark.asyncio
async def test_update_password_me_same_password(authorized_client: AsyncClient):
    """
    测试新密码与当前密码相同时失败。
    """
    response = await authorized_client.patch(
        "/v1/users/me/password",
        json={
            "current_password": "testpassword123",
            "new_password": "testpassword123",  # 与当前密码相同
        },
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "cannot be the same" in data["detail"]


# ======================== 删除当前用户测试 ========================

@pytest.mark.asyncio
async def test_delete_user_me_success(authorized_client: AsyncClient, test_user: User):
    """
    测试成功删除当前用户自己的账户。
    """
    response = await authorized_client.delete("/v1/users/me")
    
    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]


@pytest.mark.asyncio
async def test_delete_user_me_superuser(
    client: AsyncClient, 
    superuser_token: str,
    test_superuser: User
):
    """
    测试超级管理员不能删除自己的账户。
    """
    client.headers["Authorization"] = f"Bearer {superuser_token}"
    response = await client.delete("/v1/users/me")
    
    assert response.status_code == 403
    data = response.json()
    assert "not allowed to delete themselves" in data["detail"]


# ======================== 超级管理员操作测试 ========================

@pytest.mark.asyncio
async def test_read_users_superuser(
    superuser_client: AsyncClient,
    test_user: User,
    test_superuser: User
):
    """
    测试超级管理员获取所有用户列表。
    """
    response = await superuser_client.get("/v1/users/")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] >= 2
    
    # 检查返回的用户数据
    emails = [user["email"] for user in data["data"]]
    assert test_user.email in emails
    assert test_superuser.email in emails


@pytest.mark.asyncio
async def test_read_users_normal_user(authorized_client: AsyncClient):
    """
    测试拥有 user:read scope 的用户（editor）可以获取用户列表（scope 判定，非超管判定）。
    """
    response = await authorized_client.get("/v1/users/")

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data


@pytest.mark.asyncio
async def test_read_users_no_scope_forbidden(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """
    测试没有 user:read scope 的用户（viewer）读取用户列表返回 403。
    """
    from datetime import timedelta

    from app.core.security import create_access_token

    # 创建只有 user:read 之外 scope 的用户（自定义无 user:read 角色）
    limited_role = Role(name="limited_reader")
    db_session.add(limited_role)
    await db_session.flush()
    db_session.add(RoleScopeModel(role_id=limited_role.id, scope="role:read"))
    await db_session.commit()

    limited_user = User(
        email="limited_reader@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(limited_user)
    await db_session.flush()
    db_session.add(UserRole(user_id=limited_user.id, role_id=limited_role.id))
    await db_session.commit()

    token = create_access_token(subject=str(limited_user.id), expires_delta=timedelta(minutes=30))
    client.headers["Authorization"] = f"Bearer {token}"

    response = await client.get("/v1/users/")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_user_superuser(superuser_client: AsyncClient):
    """
    测试超级管理员创建新用户。
    """
    response = await superuser_client.post(
        "/v1/users/",
        json={
            "email": "created@example.com",
            "password": "createdpass123",
            "full_name": "Created User",
            "is_active": True,
            "is_superuser": False,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "created@example.com"
    assert data["full_name"] == "Created User"


@pytest.mark.asyncio
async def test_create_user_duplicate_email_superuser(
    superuser_client: AsyncClient,
    test_user: User
):
    """
    测试超级管理员创建已存在邮箱的用户失败。
    """
    response = await superuser_client.post(
        "/v1/users/",
        json={
            "email": test_user.email,  # 已存在的邮箱
            "password": "password123",
            "full_name": "Duplicate User",
        },
    )
    
    # 邮箱唯一性冲突返回 409（与 USER_EMAIL_ALREADY_EXISTS → 409 的约定一致）
    assert response.status_code == 409
    data = response.json()
    assert "already exists" in data["detail"]


@pytest.mark.asyncio
async def test_read_user_by_id_own(
    authorized_client: AsyncClient,
    test_user: User
):
    """
    测试用户获取自己的信息。
    """
    response = await authorized_client.get(f"/v1/users/{test_user.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_read_user_by_id_other_normal_user(
    authorized_client: AsyncClient,
    db_session: AsyncSession
):
    """
    测试拥有 user:read scope 的用户（editor）可以查看其他用户的信息（scope 判定，非超管判定）。
    """
    # 创建另一个用户
    other_user = User(
        email="other2@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Other User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(other_user)
    await db_session.commit()

    response = await authorized_client.get(f"/v1/users/{other_user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(other_user.id)
    assert data["email"] == other_user.email


@pytest.mark.asyncio
async def test_read_user_by_id_superuser(
    superuser_client: AsyncClient,
    test_user: User
):
    """
    测试超级管理员可以获取任何用户的信息。
    """
    response = await superuser_client.get(f"/v1/users/{test_user.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_update_user_superuser(
    superuser_client: AsyncClient,
    test_user: User
):
    """
    测试超级管理员更新其他用户信息。
    """
    response = await superuser_client.patch(
        f"/v1/users/{test_user.id}",
        json={
            "full_name": "Updated By Admin",
            "is_active": False,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated By Admin"
    assert data["is_active"] == False


@pytest.mark.asyncio
async def test_update_user_not_found_superuser(superuser_client: AsyncClient):
    """
    测试超级管理员更新不存在的用户失败。
    """
    fake_id = uuid.uuid4()
    response = await superuser_client.patch(
        f"/v1/users/{fake_id}",
        json={
            "full_name": "Updated Name",
        },
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_scope_permission(
    authorized_client: AsyncClient,
    test_user: User,
    db_session: AsyncSession
):
    """
    测试拥有 user:delete scope 的用户（editor）可以删除其他用户（scope 判定，非超管判定）。
    """
    # 创建要删除的用户
    user_to_delete = User(
        email="delete_scope@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="User To Delete By Editor",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user_to_delete)
    await db_session.commit()

    # test_user 默认 editor 角色，拥有 user:delete scope
    response = await authorized_client.delete(f"/v1/users/{user_to_delete.id}")

    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]


@pytest.mark.asyncio
async def test_delete_user_without_scope_forbidden(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """
    测试没有 user:admin / user:delete scope 的用户（viewer）删除用户返回 403。
    """
    from datetime import timedelta

    from sqlalchemy import select

    from app.core.security import create_access_token

    # 创建只有 user:read scope 的 viewer 用户
    viewer_role = (await db_session.execute(
        select(Role).where(Role.name == "viewer")
    )).scalar_one()
    limited_user = User(
        email="limited_delete@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(limited_user)
    await db_session.flush()
    db_session.add(UserRole(user_id=limited_user.id, role_id=viewer_role.id))
    await db_session.commit()

    # 创建要被删除的目标用户
    target_user = User(
        email="target_delete@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(target_user)
    await db_session.commit()

    token = create_access_token(subject=str(limited_user.id), expires_delta=timedelta(minutes=30))
    client.headers["Authorization"] = f"Bearer {token}"

    response = await client.delete(f"/v1/users/{target_user.id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_superuser(
    superuser_client: AsyncClient,
    db_session: AsyncSession
):
    """
    测试超级管理员删除其他用户。
    """
    # 创建一个要删除的用户
    user_to_delete = User(
        email="delete@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="User To Delete",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user_to_delete)
    await db_session.commit()
    
    response = await superuser_client.delete(f"/v1/users/{user_to_delete.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]


@pytest.mark.asyncio
async def test_delete_user_self_superuser(
    superuser_client: AsyncClient,
    test_superuser: User
):
    """
    测试超级管理员不能删除自己。
    """
    response = await superuser_client.delete(f"/v1/users/{test_superuser.id}")

    assert response.status_code == 403
    data = response.json()
    assert "not allowed to delete themselves" in data["detail"]


@pytest.mark.asyncio
async def test_delete_last_superuser_forbidden(
    authorized_client: AsyncClient,
    db_session: AsyncSession,
):
    """
    测试删除系统中最后一个超管被拒（最后超管保护）。

    构造：db_session 默认无任何超管，本用例创建唯一的超管 sup2。
    使用拥有 user:delete scope 的 editor（authorized_client）删除 sup2：
    - editor 拥有 user:delete scope，依赖层通过（scope 判定非超管判定）；
    - 但 service 层检测删除目标是超管且删除后系统中超管数为 0 → 拒绝 400。
    """
    # 创建唯一的超管（将要删除的目标）
    sup2 = User(
        email="sup2@example.com",
        hashed_password=get_password_hash("sup2password123"),
        full_name="Super 2",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(sup2)
    await db_session.commit()

    response = await authorized_client.delete(f"/v1/users/{sup2.id}")

    assert response.status_code == 400
    data = response.json()
    assert "last superuser" in data["detail"]

    # 超管用户确实未被删除
    still_exists = await db_session.get(User, sup2.id)
    assert still_exists is not None


@pytest.mark.asyncio
async def test_delete_superuser_when_another_exists(
    superuser_client: AsyncClient,
    test_superuser: User,
    db_session: AsyncSession,
):
    """
    测试系统中存在多个超管时，删除其中一个超管成功（非最后超管不受保护）。
    """
    # 创建第二个超管
    sup2 = User(
        email="sup2b@example.com",
        hashed_password=get_password_hash("sup2password123"),
        full_name="Super 2b",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(sup2)
    await db_session.commit()

    # test_superuser 删除 sup2：删除后仍有 test_superuser 一个超管 → 允许
    response = await superuser_client.delete(f"/v1/users/{sup2.id}")

    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]


@pytest.mark.asyncio
async def test_delete_user_not_found_superuser(superuser_client: AsyncClient):
    """
    测试超级管理员删除不存在的用户失败。
    """
    fake_id = uuid.uuid4()
    response = await superuser_client.delete(f"/v1/users/{fake_id}")
    
    assert response.status_code == 404
