import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import emails  # type: ignore
import jwt
from jinja2 import Template
from jwt.exceptions import InvalidTokenError

from app.core import security
from app.core.config import get_settings

settings = get_settings()
# 配置日志记录器
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ======================== 密码重置令牌管理 ========================

def generate_password_reset_token(email: str) -> str:
    """
    生成密码重置 JWT 令牌。
    
    参数：
    - email：用户邮箱
    
    返回值：
    - JWT 令牌字符串
    
    令牌包含：
    - exp：过期时间戳（当前时间 + EMAIL_RESET_TOKEN_EXPIRE_HOURS）
    - nbf：生效时间戳（当前时间）
    - sub：令牌主体（用户邮箱）
    
    流程：
    1. 计算过期时间（有效期：48 小时）
    2. 使用 JWT HS256 算法签名
    3. 返回令牌供邮件链接使用
    
    安全性：
    - 令牌有时间限制（nbf + exp）
    - 使用服务端 SECRET_KEY 签名，防伪造
    """
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    """
    验证密码重置令牌。
    
    参数：
    - token：密码重置 JWT 令牌
    
    返回值：
    - 邮箱字符串（令牌有效）
    - None（令牌无效、过期或签名错误）
    
    流程：
    1. 使用 settings.SECRET_KEY 解码 JWT
    2. 若解码成功，返回 sub（邮箱）
    3. 若捕获 InvalidTokenError（过期、签名错误等），返回 None
    
    用途：
    - 验证邮件中点击的重置链接中的令牌
    - 若返回邮箱，说明用户可以重置密码
    - 若返回 None，说明令牌已过期或被篡改
    """
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None
