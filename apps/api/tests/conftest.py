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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

# Import app and dependencies to override
from main import app as fastapi_app
from app.core.config import get_settings, Settings
from app.core.database import get_db
from app.core.models import User, Role, RoleScopeModel, UserRole
from app.core.security import get_password_hash, create_access_token
from app.core.dependencies import get_current_user, get_current_active_superuser
from app.core.scopes import DEFAULT_ROLE_SCOPES, ALL_ROLE_SCOPES


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

    # 初始化默认角色（viewer / editor / admin）及其 scopes
    async with async_session() as session:
        for role_name, scopes in DEFAULT_ROLE_SCOPES.items():
            role = Role(name=role_name)
            session.add(role)
            await session.flush()
            for scope_value in scopes:
                session.add(RoleScopeModel(role_id=role.id, scope=scope_value))
        await session.commit()

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
async def app(db_session: AsyncSession) -> AsyncGenerator[FastAPI, None]:
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
    创建一个普通测试用户（默认分配 editor 角色，拥有 user 读/写权限）。

    editor scopes: user:read, user:create, user:update, user:delete
    """
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.flush()

    # 默认分配 editor 角色
    role_result = await db_session.execute(select(Role).where(Role.name == "editor"))  # type: ignore[arg-type]
    role = role_result.scalar_one_or_none()
    if role:
        db_session.add(UserRole(user_id=user.id, role_id=role.id))

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
async def test_role(db_session: AsyncSession, test_user: User) -> Role:
    """
    创建一个测试角色，属于 test_role（自定义角色，可用于 CRUD 测试）。
    """
    role = Role(name="test_role")
    db_session.add(role)
    await db_session.flush()
    db_session.add(RoleScopeModel(role_id=role.id, scope="user:read"))
    await db_session.commit()
    await db_session.refresh(role)
    return role


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
async def role_admin_user(db_session: AsyncSession) -> User:
    """
    创建一个拥有全部 role:* scope 的管理用户（role_manager 自定义角色）。

    role_manager scopes: role:read, role:create, role:update, role:delete
    用于角色管理 CRUD 测试（editor 用户不再持有 role:* scope）。
    """
    role = Role(name="role_manager")
    db_session.add(role)
    await db_session.flush()
    for scope_value in ALL_ROLE_SCOPES:
        db_session.add(RoleScopeModel(role_id=role.id, scope=scope_value.value))
    await db_session.commit()

    user = User(
        email="roleadmin@example.com",
        hashed_password=get_password_hash("roleadmin123"),
        full_name="Role Admin",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def role_admin_token(role_admin_user: User) -> str:
    """
    为角色管理用户生成 JWT 访问令牌。
    """
    from datetime import timedelta
    token = create_access_token(
        subject=str(role_admin_user.id),
        expires_delta=timedelta(minutes=30),
    )
    return token


@pytest_asyncio.fixture(scope="function")
async def role_admin_client(app: FastAPI, role_admin_token: str) -> AsyncGenerator[AsyncClient, None]:
    """
    已授权的角色管理客户端（拥有全部 role:* scope）。
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers["Authorization"] = f"Bearer {role_admin_token}"
        yield ac


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
