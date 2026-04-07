"""
Tests for login and authentication endpoints.

Covers:
- OAuth2 token login (/login/access-token)
- Token validation (/login/test-token)
- Password reset (/reset-password/)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User
from app.core.security import create_access_token
from app.domains.user.repository import create_user
from app.domains.user.schemas import UserCreate


class TestLoginAccessToken:
    """Tests for /login/access-token endpoint."""

    async def test_login_success(self, client: AsyncClient, normal_user: User):
        """Test successful login with valid credentials."""
        response = await client.post(
            "/v1/login/access-token",
            data={
                "username": normal_user.email,
                "password": "userpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    async def test_login_wrong_password(self, client: AsyncClient, normal_user: User):
        """Test login with wrong password returns 400."""
        response = await client.post(
            "/v1/login/access-token",
            data={
                "username": normal_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 400
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user returns 400."""
        response = await client.post(
            "/v1/login/access-token",
            data={
                "username": "nonexistent@example.com",
                "password": "somepassword",
            },
        )
        assert response.status_code == 400
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_login_inactive_user(self, client: AsyncClient, inactive_user: User):
        """Test login with inactive user returns 400."""
        response = await client.post(
            "/v1/login/access-token",
            data={
                "username": inactive_user.email,
                "password": "inactivepassword123",
            },
        )
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]


class TestLoginTestToken:
    """Tests for /login/test-token endpoint."""

    async def test_test_token_valid(self, client: AsyncClient, normal_user_token: str, normal_user: User):
        """Test token validation with valid token."""
        response = await client.post(
            "/v1/login/test-token",
            headers={"Authorization": f"Bearer {normal_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == normal_user.email
        assert data["id"] == str(normal_user.id)
        assert "hashed_password" not in data  # Should not expose password

    async def test_test_token_invalid(self, client: AsyncClient):
        """Test token validation with invalid token returns 403."""
        response = await client.post(
            "/v1/login/test-token",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 403

    async def test_test_token_no_token(self, client: AsyncClient):
        """Test token validation without token returns 401."""
        response = await client.post("/v1/login/test-token")
        assert response.status_code == 401

    async def test_test_token_expired(self, client: AsyncClient, normal_user: User):
        """Test token validation with expired token returns 403."""
        from datetime import timedelta
        # Create an expired token (negative expiry)
        expired_token = create_access_token(
            subject=str(normal_user.id),
            expires_delta=timedelta(seconds=-1),
        )
        response = await client.post(
            "/v1/login/test-token",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 403


class TestResetPassword:
    """Tests for /reset-password/ endpoint."""

    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Test password reset with invalid token returns 400."""
        response = await client.post(
            "/v1/reset-password/",
            json={
                "token": "invalid-token",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 400
        assert "Invalid token" in response.json()["detail"]

    async def test_reset_password_short_password(self, client: AsyncClient):
        """Test password reset with short password returns validation error."""
        response = await client.post(
            "/v1/reset-password/",
            json={
                "token": "some-token",
                "new_password": "short",
            },
        )
        # Should fail validation (password too short)
        assert response.status_code == 422
