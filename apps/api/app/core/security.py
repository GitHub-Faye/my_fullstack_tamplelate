from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import get_settings
from fastapi.security import OAuth2PasswordBearer
password_hash = PasswordHash(
    (
        Argon2Hasher(),
        BcryptHasher(),
    )
)


settings = get_settings()



# ======================== OAuth2 配置 ========================
# 定义 OAuth2 密码流。tokenUrl 指向获取令牌的 API 端点
# FastAPI 自动使用此配置生成 OpenAPI 文档中的"Authorize"按钮
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)




def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    """
    生成 JWT 访问令牌。
    
    参数：
    - subject：令牌主体，通常是用户 ID（UUID）
    - expires_delta：有效期时长（timedelta）
    
    返回值：
    - JWT 字符串
    
    JWT 包含：
    - exp：过期时间戳
    - sub：用户标识
    """
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    """
    验证明文密码和哈希密码是否匹配。
    
    参数：
    - plain_password：用户输入的明文密码
    - hashed_password：数据库中存储的哈希密码
    
    返回值：
    - 元组 (是否验证正确, 升级后的哈希值或 None)
    
    核心特性：
    - verify_and_update()：验证同时检测是否需要升级哈希（如从 Bcrypt 升级到 Argon2）
    - 若返回新哈希值，需在 CRUD 中更新数据库
    - 这实现了"密钥拉伸升级"机制，保持安全性与兼容性的平衡
    """
    return password_hash.verify_and_update(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    对明文密码进行哈希。
    
    参数：
    - password：明文密码
    
    返回值：
    - Argon2 哈希值
    
    说明：
    - 使用 PasswordHash 配置中的首个算法（Argon2）
    - Argon2 参数遵循 OWASP 推荐默认值
    """
    return password_hash.hash(password)
