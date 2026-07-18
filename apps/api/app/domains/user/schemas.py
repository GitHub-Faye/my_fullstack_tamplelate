import uuid
from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from app.core.schemas import PaginatedResponse
from app.core.models import UserRoleType


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


# 管理员创建用户（支持角色和工资字段）
class UserAdminCreate(SQLModel):
    """管理员创建工程师/PM 账号"""
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRoleType = Field(default=UserRoleType.ENGINEER, description="用户角色")
    is_active: bool = True
    # 工程师工资字段
    S0: float | None = Field(default=None, ge=0)
    H0: float | None = Field(default=None, ge=0)
    T_monthly_plan: float | None = Field(default=None, ge=0)
    # PM 工资字段
    S_base: float | None = Field(default=None, ge=0)
    S_assess: float | None = Field(default=None, ge=0)
    R_base: float | None = Field(default=None, ge=0, le=1)
    R_assess: float | None = Field(default=None, ge=0, le=1)
    baseline_client_count: int | None = Field(default=None, ge=0)


# 管理员更新用户
class UserAdminUpdate(SQLModel):
    """管理员更新用户信息"""
    email: EmailStr | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    role: UserRoleType | None = None
    # 工程师工资字段
    S0: float | None = Field(default=None, ge=0)
    H0: float | None = Field(default=None, ge=0)
    T_monthly_plan: float | None = Field(default=None, ge=0)
    # PM 工资字段
    S_base: float | None = Field(default=None, ge=0)
    S_assess: float | None = Field(default=None, ge=0)
    R_base: float | None = Field(default=None, ge=0, le=1)
    R_assess: float | None = Field(default=None, ge=0, le=1)
    baseline_client_count: int | None = Field(default=None, ge=0)


# 启用/禁用用户
class UserToggleActive(SQLModel):
    is_active: bool


# 管理员重置密码
class AdminPasswordReset(SQLModel):
    new_password: str = Field(min_length=8, max_length=128)


# ---------------------------- API 响应模型（Response DTO） --------------------------------
# 返回给客户端的 User 信息
class UserPublic(UserBase):
    id: uuid.UUID
    role: UserRoleType
    created_at: datetime | None = None


# 管理员视图的用户详情（包含工资字段）
class UserAdminDetail(UserPublic):
    S0: float | None = None
    H0: float | None = None
    T_monthly_plan: float | None = None
    current_starpoint: int = 0
    S_base: float | None = None
    S_assess: float | None = None
    R_base: float | None = None
    R_assess: float | None = None
    baseline_client_count: int | None = None


# 使用统一分页协议
class UsersPublic(PaginatedResponse[UserPublic]):
    pass


class UsersAdminPublic(PaginatedResponse[UserAdminDetail]):
    pass


# ---------------------------- 审计日志 DTO --------------------------------

class AuditLogPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    target_type: str
    target_id: str | None = None
    details: str | None = None
    ip_address: str | None = None
    created_at: datetime | None = None
    operator_name: str | None = None


class AuditLogList(PaginatedResponse[AuditLogPublic]):
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
