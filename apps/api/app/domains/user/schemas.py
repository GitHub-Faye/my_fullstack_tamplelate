import uuid
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from app.core.schemas import  PaginatedResponse


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
# 不继承 UserBase：父类字段为必填，此处需要全部可选（部分更新），
# 独立声明避免用 type: ignore 覆盖父类字段的反模式。
class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
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
    # 用户当前拥有的权限 scope 列表（由 read_user_me 等端点填充，用于前端 scope 级权限控制）
    scopes: list[str] = []


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
