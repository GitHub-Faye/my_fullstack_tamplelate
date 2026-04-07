"""
Tests for user management endpoints.

Covers:
- User registration (/users/signup)
- Get current user (/users/me)
- Update current user (/users/me)
- Update password (/users/me/password)
- Delete current user (/users/me)
- List users - superuser only (/users/)
- Create user - superuser only (/users/)
- Get user by ID (/users/{id})
- Update user - superuser only (/users/{id})
- Delete user - superuser only (/users/{id})
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User
from app.domains.user.repository import create_user, get_user_by_email
from app.domains.user.schemas import UserCreate


class TestUserSignup:
    """Tests for /users/signup endpoint."""

    async def test_signup_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful user registration."""
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
        assert data["is_active"] is True
        assert data["is_superuser"] is False

        # Verify user was created in database
        user = await get_user_by_email(session=db_session, email="newuser@example.com")
        assert user is not None
        assert user.email == "newuser@example.com"

    async def test_signup_duplicate_email(self, client: AsyncClient, normal_user: User):
        """Test registration with duplicate email returns 400."""
        response = await client.post(
            "/v1/users/signup",
            json={
                "email": normal_user.email,
                "password": "newpassword123",
                "full_name": "Another User",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    async def test_signup_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email returns 422."""
        response = await client.post(
            "/v1/users/signup",
            json={
                "email": "not-an-email",
                "password": "newpassword123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 422

    async def test_signup_short_password(self, client: AsyncClient):
        """Test registration with short password returns 422."""
        response = await client.post(
            "/v1/users/signup",
            json={
                "email": "newuser@example.com",
                "password": "short",
                "full_name": "New User",
            },
        )
        assert response.status_code == 422


class TestGetCurrentUser:
    """Tests for /users/me endpoint."""

    async def test_get_me_success(self, authorized_client: AsyncClient, normal_user: User):
        """Test getting current user info."""
        response = await authorized_client.get("/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == normal_user.email
        assert data["id"] == str(normal_user.id)
        assert "hashed_password" not in data

    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Test getting current user without token returns 401."""
        response = await client.get("/v1/users/me")
        assert response.status_code == 401


class TestUpdateCurrentUser:
    """Tests for PATCH /users/me endpoint."""

    async def test_update_me_success(self, authorized_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test updating current user info."""
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

    async def test_update_me_email_conflict(self, authorized_client: AsyncClient, superuser: User):
        """Test updating email to one that exists returns 409."""
        response = await authorized_client.patch(
            "/v1/users/me",
            json={
                "email": superuser.email,
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    async def test_update_me_unauthorized(self, client: AsyncClient):
        """Test updating current user without token returns 401."""
        response = await client.patch(
            "/v1/users/me",
            json={"full_name": "Updated Name"},
        )
        assert response.status_code == 401


class TestUpdatePassword:
    """Tests for PATCH /users/me/password endpoint."""

    async def test_update_password_success(self, authorized_client: AsyncClient, normal_user: User, client: AsyncClient):
        """Test updating password successfully."""
        response = await authorized_client.patch(
            "/v1/users/me/password",
            json={
                "current_password": "userpassword123",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 200
        assert "updated successfully" in response.json()["message"]

        # Verify can login with new password
        login_response = await client.post(
            "/v1/login/access-token",
            data={
                "username": normal_user.email,
                "password": "newpassword456",
            },
        )
        assert login_response.status_code == 200

    async def test_update_password_wrong_current(self, authorized_client: AsyncClient):
        """Test updating password with wrong current password returns 400."""
        response = await authorized_client.patch(
            "/v1/users/me/password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 400
        assert "Incorrect password" in response.json()["detail"]

    async def test_update_password_same_as_current(self, authorized_client: AsyncClient):
        """Test updating password to same as current returns 400."""
        response = await authorized_client.patch(
            "/v1/users/me/password",
            json={
                "current_password": "userpassword123",
                "new_password": "userpassword123",
            },
        )
        assert response.status_code == 400
        assert "cannot be the same" in response.json()["detail"]

    async def test_update_password_unauthorized(self, client: AsyncClient):
        """Test updating password without token returns 401."""
        response = await client.patch(
            "/v1/users/me/password",
            json={
                "current_password": "oldpass",
                "new_password": "newpass123",
            },
        )
        assert response.status_code == 401


class TestDeleteCurrentUser:
    """Tests for DELETE /users/me endpoint."""

    async def test_delete_me_success(self, authorized_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test deleting current user account."""
        response = await authorized_client.delete("/v1/users/me")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify user was deleted
        user = await get_user_by_email(session=db_session, email=normal_user.email)
        assert user is None

    async def test_delete_me_superuser_forbidden(self, superuser_client: AsyncClient):
        """Test superuser cannot delete themselves returns 403."""
        response = await superuser_client.delete("/v1/users/me")
        assert response.status_code == 403
        assert "not allowed to delete themselves" in response.json()["detail"]

    async def test_delete_me_unauthorized(self, client: AsyncClient):
        """Test deleting current user without token returns 401."""
        response = await client.delete("/v1/users/me")
        assert response.status_code == 401


class TestListUsers:
    """Tests for GET /users/ endpoint (superuser only)."""

    async def test_list_users_as_superuser(self, superuser_client: AsyncClient, normal_user: User):
        """Test listing users as superuser."""
        response = await superuser_client.get("/v1/users/")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data
        assert data["count"] >= 1
        assert len(data["data"]) >= 1

    async def test_list_users_pagination(self, superuser_client: AsyncClient):
        """Test listing users with pagination."""
        response = await superuser_client.get("/v1/users/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 10

    async def test_list_users_as_normal_user(self, authorized_client: AsyncClient):
        """Test listing users as normal user returns 403."""
        response = await authorized_client.get("/v1/users/")
        assert response.status_code == 403

    async def test_list_users_unauthorized(self, client: AsyncClient):
        """Test listing users without token returns 401."""
        response = await client.get("/v1/users/")
        assert response.status_code == 401


class TestCreateUser:
    """Tests for POST /users/ endpoint (superuser only)."""

    async def test_create_user_as_superuser(self, superuser_client: AsyncClient, db_session: AsyncSession):
        """Test creating user as superuser."""
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

    async def test_create_user_duplicate_email(self, superuser_client: AsyncClient, normal_user: User):
        """Test creating user with duplicate email returns 400."""
        response = await superuser_client.post(
            "/v1/users/",
            json={
                "email": normal_user.email,
                "password": "newpass123",
                "full_name": "Duplicate User",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    async def test_create_user_as_normal_user(self, authorized_client: AsyncClient):
        """Test creating user as normal user returns 403."""
        response = await authorized_client.post(
            "/v1/users/",
            json={
                "email": "new@example.com",
                "password": "newpass123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 403


class TestGetUserById:
    """Tests for GET /users/{id} endpoint."""

    async def test_get_user_by_id_self(self, authorized_client: AsyncClient, normal_user: User):
        """Test getting own user info by ID."""
        response = await authorized_client.get(f"/v1/users/{normal_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == normal_user.email
        assert data["id"] == str(normal_user.id)

    async def test_get_user_by_id_as_superuser(self, superuser_client: AsyncClient, normal_user: User):
        """Test getting other user info as superuser."""
        response = await superuser_client.get(f"/v1/users/{normal_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == normal_user.email

    async def test_get_user_by_id_other_user_forbidden(self, authorized_client: AsyncClient, superuser: User):
        """Test getting other user info as normal user returns 403."""
        response = await authorized_client.get(f"/v1/users/{superuser.id}")
        assert response.status_code == 403

    async def test_get_user_by_id_not_found(self, superuser_client: AsyncClient):
        """Test getting non-existent user returns 404."""
        fake_id = uuid.uuid4()
        response = await superuser_client.get(f"/v1/users/{fake_id}")
        assert response.status_code == 404


class TestUpdateUser:
    """Tests for PATCH /users/{id} endpoint (superuser only)."""

    async def test_update_user_as_superuser(self, superuser_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test updating user as superuser."""
        response = await superuser_client.patch(
            f"/v1/users/{normal_user.id}",
            json={
                "full_name": "Updated By Superuser",
                "is_active": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated By Superuser"
        assert data["is_active"] is False

    async def test_update_user_not_found(self, superuser_client: AsyncClient):
        """Test updating non-existent user returns 404."""
        fake_id = uuid.uuid4()
        response = await superuser_client.patch(
            f"/v1/users/{fake_id}",
            json={"full_name": "Updated Name"},
        )
        assert response.status_code == 404

    async def test_update_user_as_normal_user(self, authorized_client: AsyncClient, superuser: User):
        """Test updating user as normal user returns 403."""
        response = await authorized_client.patch(
            f"/v1/users/{superuser.id}",
            json={"full_name": "Hacked Name"},
        )
        assert response.status_code == 403


class TestDeleteUser:
    """Tests for DELETE /users/{id} endpoint (superuser only)."""

    async def test_delete_user_as_superuser(self, superuser_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test deleting user as superuser."""
        response = await superuser_client.delete(f"/v1/users/{normal_user.id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify user was deleted
        user = await get_user_by_email(session=db_session, email=normal_user.email)
        assert user is None

    async def test_delete_user_self_forbidden(self, superuser_client: AsyncClient, superuser: User):
        """Test superuser deleting themselves returns 403."""
        response = await superuser_client.delete(f"/v1/users/{superuser.id}")
        assert response.status_code == 403
        assert "not allowed to delete themselves" in response.json()["detail"]

    async def test_delete_user_not_found(self, superuser_client: AsyncClient):
        """Test deleting non-existent user returns 404."""
        fake_id = uuid.uuid4()
        response = await superuser_client.delete(f"/v1/users/{fake_id}")
        assert response.status_code == 404

    async def test_delete_user_as_normal_user(self, authorized_client: AsyncClient, superuser: User):
        """Test deleting user as normal user returns 403."""
        response = await authorized_client.delete(f"/v1/users/{superuser.id}")
        assert response.status_code == 403
