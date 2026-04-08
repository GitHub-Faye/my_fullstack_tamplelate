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

from app.core.models import User
from app.core.security import get_password_hash


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
    
    assert response.status_code == 400
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
    测试普通用户无法获取所有用户列表。
    """
    response = await authorized_client.get("/v1/users/")
    
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
    
    assert response.status_code == 400
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
    测试普通用户无法获取其他用户的信息。
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
    
    assert response.status_code == 403
    data = response.json()
    assert "privileges" in data["detail"]


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
async def test_delete_user_not_found_superuser(superuser_client: AsyncClient):
    """
    测试超级管理员删除不存在的用户失败。
    """
    fake_id = uuid.uuid4()
    response = await superuser_client.delete(f"/v1/users/{fake_id}")
    
    assert response.status_code == 404
