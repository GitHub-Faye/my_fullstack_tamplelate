"""
Pytest configuration and shared fixtures for FastAPI testing.

This module provides:
- Async test support with pytest-asyncio
- In-memory SQLite database for testing (no external DB needed)
- FastAPI dependency overrides for database and authentication
- Test client fixtures using httpx.AsyncClient
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

# Import app and dependencies to override
from main import app as fastapi_app
from app.core.config import get_settings, Settings
from app.core.database import get_db
from app.core.models import User, Item
from app.core.security import get_password_hash, create_access_token
from apps.api.app.domains.item.dependencies import get_current_user, get_current_active_superuser


# ======================== pytest-asyncio 配置 ========================

# 配置 pytest-asyncio 使用 function scope
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ======================== 内存数据库配置 ========================

# 使用 aiosqlite 作为内存数据库，无需外部 PostgreSQL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def engine():
    """
    创建测试用的异步数据库引擎（function 级别，每个测试函数独立）。
    
    使用内存中的 SQLite 数据库，无需外部数据库服务器。
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # 测试时关闭 SQL 打印
        future=True,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    为每个测试函数创建独立的数据库会话。
    
    每个测试函数都会：
    1. 创建新的数据库表
    2. 运行测试
    3. 回滚事务并删除表
    
    确保测试之间完全隔离。
    """
    # 创建会话工厂
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # 创建会话
    async with async_session() as session:
        yield session
        # 测试结束后回滚
        await session.rollback()
    
    # 清理表
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


# ======================== FastAPI App Fixture ========================

@pytest_asyncio.fixture(scope="function")
async def app(db_session: AsyncSession) -> FastAPI:
    """
    创建配置好的 FastAPI 应用实例，用于测试。
    
    覆盖的依赖：
    - get_db: 返回内存数据库会话
    """
    # 覆盖数据库依赖
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
    
    # 覆盖依赖
    fastapi_app.dependency_overrides[get_db] = override_get_db
    
    yield fastapi_app
    
    # 清理依赖覆盖
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    创建 httpx.AsyncClient 测试客户端。
    
    使用 ASGITransport 直接调用 FastAPI 应用，无需启动服务器。
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ======================== 测试数据 Fixtures ========================

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """
    创建一个普通测试用户。
    """
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_superuser(db_session: AsyncSession) -> User:
    """
    创建一个超级管理员测试用户。
    """
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_item(db_session: AsyncSession, test_user: User) -> Item:
    """
    创建一个测试物品，属于 test_user。
    """
    item = Item(
        title="Test Item",
        description="This is a test item",
        owner_id=test_user.id,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest_asyncio.fixture(scope="function")
async def user_token(test_user: User) -> str:
    """
    为普通测试用户生成 JWT 访问令牌。
    """
    from datetime import timedelta
    token = create_access_token(
        subject=str(test_user.id),
        expires_delta=timedelta(minutes=30),
    )
    return token


@pytest_asyncio.fixture(scope="function")
async def superuser_token(test_superuser: User) -> str:
    """
    为超级管理员测试用户生成 JWT 访问令牌。
    """
    from datetime import timedelta
    token = create_access_token(
        subject=str(test_superuser.id),
        expires_delta=timedelta(minutes=30),
    )
    return token


@pytest_asyncio.fixture(scope="function")
async def authorized_client(app: FastAPI, user_token: str) -> AsyncGenerator[AsyncClient, None]:
    """
    已授权的客户端（普通用户）。
    
    自动在请求头中添加 Authorization。
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers["Authorization"] = f"Bearer {user_token}"
        yield ac


@pytest_asyncio.fixture(scope="function")
async def superuser_client(app: FastAPI, superuser_token: str) -> AsyncGenerator[AsyncClient, None]:
    """
    已授权的客户端（超级管理员）。
    
    自动在请求头中添加 Authorization。
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers["Authorization"] = f"Bearer {superuser_token}"
        yield ac


# ======================== 同步客户端 Fixture ========================

@pytest_asyncio.fixture(scope="function")
async def sync_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    同步测试客户端（使用 httpx.AsyncClient）。
    
    用于需要同步接口的测试场景。
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
