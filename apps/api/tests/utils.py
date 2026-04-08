"""
Utility functions for testing.

提供测试辅助函数，如用户创建、token 生成等。
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User
from app.core.security import get_password_hash, create_access_token


async def create_test_user(
    session: AsyncSession,
    email: str = "test@example.com",
    password: str = "testpassword123",
    full_name: str = "Test User",
    is_active: bool = True,
    is_superuser: bool = False,
) -> User:
    """
    创建一个测试用户。
    
    Args:
        session: 数据库会话
        email: 用户邮箱
        password: 明文密码（会被哈希）
        full_name: 用户全名
        is_active: 是否激活
        is_superuser: 是否超级管理员
    
    Returns:
        创建的用户对象
    """
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        is_active=is_active,
        is_superuser=is_superuser,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


def create_test_token(user_id: uuid.UUID, expires_minutes: int = 30) -> str:
    """
    为测试用户创建访问令牌。
    
    Args:
        user_id: 用户 ID
        expires_minutes: 令牌过期时间（分钟）
    
    Returns:
        JWT 令牌字符串
    """
    return create_access_token(
        subject=str(user_id),
        expires_delta=timedelta(minutes=expires_minutes),
    )


def get_auth_headers(token: str) -> dict[str, str]:
    """
    获取包含认证信息的请求头。
    
    Args:
        token: JWT 令牌
    
    Returns:
        包含 Authorization 头的字典
    """
    return {"Authorization": f"Bearer {token}"}
