"""
依赖注入模块（Dependency Injection）

管理 FastAPI 的所有依赖项：
- 数据库会话管理
- OAuth2 令牌认证
- 用户身份验证和权限检查
- 类型别名定义（用于路由端点）

核心概念：
- 依赖注入(DI)：将依赖项作为函数参数，FastAPI 自动解析和注入
- Annotated：Python 3.9+ 特性，用于组合类型提示和元数据
"""

import uuid
from typing import Annotated
from typing import AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, status

from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db 
from app.core.models import User
from app.core.security import reusable_oauth2

from app.domains.user.schemas import TokenPayload


settings = get_settings()


# ======================== 类型别名定义 ========================
# 使用 Annotated 组合类型提示和依赖项，提高代码重用性和可读性
# Annotated[T, Depends(...)] 模式是 FastAPI 推荐的做法

# 数据库会话类型别名
# 用途：路由中使用 session: SessionDep 自动注入数据库会话
# 等效于：session: Annotated[AsyncSession, Depends(get_db)]
SessionDep = Annotated[AsyncSession, Depends(get_db)]

# OAuth2 令牌类型别名
# 用途：路由中使用 token: TokenDep 自动从请求头提取 Bearer 令牌
# 等效于：token: Annotated[str, Depends(reusable_oauth2)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


# ======================== 用户认证 ========================

async def get_current_user(session: SessionDep, token: TokenDep) -> User:
    """
    获取当前用户（通过 JWT 令牌认证）。
    
    此函数是核心认证逻辑，所有需要登录的端点都依赖此函数。
    
    参数：
    - session：数据库会话（依赖注入）
    - token：OAuth2 Bearer 令牌（从 Authorization 请求头提取）
    
    返回值：
    - User：认证成功的用户对象
    
    业务流程：
    1. 使用 jwt.decode() 解码 JWT 令牌（验证签名和过期时间）
    2. 将译码结果构造为 TokenPayload 对象（包含 sub 字段 = 用户 ID）
    3. 从数据库查询该用户
    4. 检查用户是否已激活（is_active）
    5. 返回用户对象或抛出异常
    
    异常处理：
    - 403 Forbidden：令牌无效、过期、签名错误、格式错误
    - 404 Not Found：令牌中的用户 ID 不存在
    - 400 Bad Request：用户已被禁用（is_active=False）
    
    安全特性：
    - JWT 签名验证：防止令牌被篡改
    - 过期时间检查：令牌过期自动拒绝
    - 用户状态检查：禁用用户无法使用旧令牌
    """
    try:
        # 解码 JWT 令牌，使用 settings.SECRET_KEY 验证签名
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # 将载荷转换为 TokenPayload 数据类（包含 sub 字段）
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        # 令牌无效、过期或签名错误
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    # 从数据库查询用户
    # token_data.sub 包含用户 ID（UUID 字符串），需要转换为 UUID 对象
    user_id = uuid.UUID(token_data.sub) if isinstance(token_data.sub, str) else token_data.sub
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 检查用户是否被激活
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


# 当前用户类型别名
# 用途：路由中使用 current_user: CurrentUser 自动完成认证并注入用户对象
# 等效于：current_user: Annotated[User, Depends(get_current_user)]
CurrentUser = Annotated[User, Depends(get_current_user)]


# ======================== 权限检查 ========================

async def get_current_active_superuser(current_user: CurrentUser) -> User:
    """
    检查当前用户是否有超管权限。
    
    此函数通常在路由的 dependencies 参数中使用，用于强制权限检查。
    
    参数：
    - current_user：已认证的当前用户（依赖注入，通过 get_current_user 获取）
    
    返回值：
    - User：超管用户对象
    
    异常：
    - 403 Forbidden：用户不是超管
    
    典型使用场景：
    @router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
    def delete_user(...):
        # 只有超管可以执行此操作
        pass
    
    或者：
    @router.delete("/{user_id}")
    def delete_user(current_user: CurrentUser):
        # 手动检查
        get_current_active_superuser(current_user)
    
    两种方式等效，第一种更清晰（直接拒绝权限不足的请求）。
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
