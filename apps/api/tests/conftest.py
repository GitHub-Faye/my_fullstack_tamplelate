"""
Pytest configuration and fixtures for API tests.

This module provides:
- Test database setup with SQLite (in-memory) for fast tests
- Async HTTP client (httpx) for API testing
- User fixtures (normal user, superuser)
- Authentication helpers
"""

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.core.config import Settings
from app.core.database import get_db
from app.core.models import User
from app.core.security import get_password_hash
from app.domains.user.repository import create_user
from app.domains.user.schemas import UserCreate
from main import app


# ======================== Test Database Configuration ========================

# Use SQLite file-based database for tests (more reliable than in-memory with async)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


def get_test_settings() -> Settings:
    """Return test settings with test database."""
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        SECRET_KEY="test-secret-key-for-testing-only-do-not-use-in-production",
        FIRST_SUPERUSER="admin@example.com",
        FIRST_SUPERUSER_PASSWORD="admin12345",
        ENVIRONMENT="local",
        DEBUG=True,
    )


# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    future=True,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override database dependency for testing."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


# ======================== Pytest Configuration ========================

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database() -> AsyncGenerator[None, None]:
    """Set up test database - create all tables before tests and drop after."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    # Drop all tables after tests
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await test_engine.dispose()

    # Clean up test database file
    import os
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest_asyncio.fixture(autouse=True)
async def clean_tables() -> AsyncGenerator[None, None]:
    """Clean tables before each test to ensure test isolation."""
    yield
    # Clean up after each test
    async with test_engine.begin() as conn:
        # Delete all data from tables (keep table structure)
        await conn.exec_driver_sql("DELETE FROM item")
        await conn.exec_driver_sql("DELETE FROM user")


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with async_session() as session:
        yield session


# ======================== HTTP Client Fixtures ========================

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing."""
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up dependency override
    app.dependency_overrides.clear()


# ======================== User Fixtures ========================

@pytest_asyncio.fixture
async def normal_user(db_session: AsyncSession) -> User:
    """Create a normal (non-superuser) user for testing."""
    user_in = UserCreate(
        email="user@example.com",
        password="userpassword123",
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    user = await create_user(session=db_session, user_create=user_in)
    return user


@pytest_asyncio.fixture
async def superuser(db_session: AsyncSession) -> User:
    """Create a superuser for testing."""
    user_in = UserCreate(
        email="superuser@example.com",
        password="superpassword123",
        full_name="Test Superuser",
        is_active=True,
        is_superuser=True,
    )
    user = await create_user(session=db_session, user_create=user_in)
    return user


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Create an inactive user for testing."""
    user_in = UserCreate(
        email="inactive@example.com",
        password="inactivepassword123",
        full_name="Inactive User",
        is_active=False,
        is_superuser=False,
    )
    user = await create_user(session=db_session, user_create=user_in)
    return user


# ======================== Authentication Helpers ========================

async def get_user_token(client: AsyncClient, email: str, password: str) -> str:
    """Get access token for a user."""
    response = await client.post(
        "/v1/login/access-token",
        data={
            "username": email,
            "password": password,
        },
    )
    assert response.status_code == 200, f"Failed to get token: {response.text}"
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def normal_user_token(client: AsyncClient, normal_user: User) -> str:
    """Get access token for the normal user."""
    return await get_user_token(client, normal_user.email, "userpassword123")


@pytest_asyncio.fixture
async def superuser_token(client: AsyncClient, superuser: User) -> str:
    """Get access token for the superuser."""
    return await get_user_token(client, superuser.email, "superpassword123")


# ======================== Authenticated Client Fixtures ========================

@pytest_asyncio.fixture
async def authorized_client(client: AsyncClient, normal_user_token: str) -> AsyncClient:
    """Provide an HTTP client authorized as a normal user."""
    client.headers["Authorization"] = f"Bearer {normal_user_token}"
    return client


@pytest_asyncio.fixture
async def superuser_client(client: AsyncClient, superuser_token: str) -> AsyncClient:
    """Provide an HTTP client authorized as a superuser."""
    client.headers["Authorization"] = f"Bearer {superuser_token}"
    return client
