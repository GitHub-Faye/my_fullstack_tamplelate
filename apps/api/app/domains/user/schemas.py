import uuid
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from app.core.schemas import Message, PaginatedResponse


# ------------------------------- 用户模型 -------------------------------------------------
# 共享属性
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)  # 用户唯一邮箱
    is_active: bool = True  # 是否激活
    is_superuser: bool = False  # 是否超管
    full_name: str | None = Field(default=None, max_length=255)  # 真实姓名


# --------------------------- API 请求模型（Request DTO） -----------------------------------
# 创建用户时需要的属性
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)  # 明文密码，最少8位


# 注册接口的 DTO（与 UserCreate 区分开更清晰）
class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# 更新用户时可选属性
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


# 当前用户自更新
class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


# 修改密码参数
class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# ---------------------------- API 响应模型（Response DTO） --------------------------------
# 返回给客户端的 User 信息
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


# 使用统一分页协议
class UsersPublic(PaginatedResponse[UserPublic]):
    pass

# ---------------------------- 通用 DTO --------------------------------------------------
# Message 从 app.core.schemas 导入


# token 响应
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# JWT 载荷
class TokenPayload(SQLModel):
    sub: str | None = None


# 重置密码时的 payload
class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
