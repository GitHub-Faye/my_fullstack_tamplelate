"""
Tests for user authentication endpoints.

Tests cover:
- Login with access token (OAuth2)
- Test token validation
- Password reset functionality
"""

import pytest
from app.core.models import User
from app.core.security import get_password_hash
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# ======================== 登录测试 ========================

@pytest.mark.asyncio
async def test_login_access_token_success(client: AsyncClient, test_user: User):
    """
    测试使用正确的邮箱和密码登录成功。
    """
    response = await client.post(
        "/v1/login/access-token",
        data={
            "username": test_user.email,
            "password": "testpassword123",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_access_token_wrong_password(client: AsyncClient, test_user: User):
    """
    测试使用错误的密码登录失败。
    """
    response = await client.post(
        "/v1/login/access-token",
        data={
            "username": test_user.email,
            "password": "wrongpassword",
        },
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Incorrect email or password" in data["detail"]


@pytest.mark.asyncio
async def test_login_access_token_nonexistent_user(client: AsyncClient):
    """
    测试使用不存在的用户登录失败。
    """
    response = await client.post(
        "/v1/login/access-token",
        data={
            "username": "nonexistent@example.com",
            "password": "somepassword",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "Incorrect email or password" in data["detail"]


@pytest.mark.asyncio
async def test_login_access_token_inactive_user(
    client: AsyncClient, 
    db_session: AsyncSession
):
    """
    测试使用未激活的用户登录失败。
    """
    # 创建未激活用户
    inactive_user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Inactive User",
        is_active=False,
        is_superuser=False,
    )
    db_session.add(inactive_user)
    await db_session.commit()
    
    response = await client.post(
        "/v1/login/access-token",
        data={
            "username": inactive_user.email,
            "password": "password123",
        },
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Inactive user" in data["detail"]


# ======================== Token 验证测试 ========================

@pytest.mark.asyncio
async def test_test_token_valid(authorized_client: AsyncClient, test_user: User):
    """
    测试使用有效的 token 获取当前用户信息。
    """
    response = await authorized_client.post("/v1/login/test-token")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


@pytest.mark.asyncio
async def test_test_token_no_token(client: AsyncClient):
    """
    测试没有提供 token 时访问受保护端点失败。
    """
    response = await client.post("/v1/login/test-token")
    
    # OAuth2 returns 401 when no token is provided
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_test_token_invalid_token(client: AsyncClient):
    """
    测试使用无效的 token 访问受保护端点失败。
    """
    client.headers["Authorization"] = "Bearer invalid_token"
    response = await client.post("/v1/login/test-token")
    
    assert response.status_code == 401
    data = response.json()
    assert "Could not validate credentials" in data["detail"]


# ======================== 密码重置测试 ========================

# 注：当前应用未实现密码重置（/v1/reset-password/）功能，原模板遗留的
# test_reset_password_invalid_token 已随功能移除而删除。
