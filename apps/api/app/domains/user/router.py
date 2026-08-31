"""
用户领域 API 路由模块

提供完整的用户管理 RESTful API 端点：
- 登录认证（OAuth2 令牌 / 令牌验证）
- 获取/创建/更新/删除用户
- 密码修改
- 用户自助注册/个人信息更新
- 权限控制（超管-only 端点）
"""

import uuid
from typing import Annotated, Any

from app.core.config import get_settings
from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_any_scope,
    require_scope,
)
from app.core.responses import paginated_fields, user_public, users_public
from app.core.schemas import Message, PaginationParams
from app.core.scopes import UserScope
from app.domains.user import service
from app.domains.user.schemas import (
    Token,
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from fastapi import APIRouter, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm

# 注：已移除 Celery 异步任务（app.tasks 已删除），注册后不再派发后台任务

settings = get_settings()
# ======================== APIRouter 创建 ========================
router = APIRouter()


# ======================== 登录认证 ========================

@router.post("/login/access-token")
async def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 兼容的令牌登录：验证邮箱密码，签发访问令牌。

    参数：
    - session：数据库会话
    - form_data：OAuth2 表单（username=邮箱，password=密码）

    返回值：
    - Token：访问令牌（JWT）

    异常：
    - 400：邮箱或密码错误 / 用户未激活
    """
    return await service.login(
        session=session,
        email=form_data.username,
        password=form_data.password,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@router.post("/login/test-token", response_model=UserPublic)
async def test_token(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    校验访问令牌并返回当前用户信息（含权限 scope 列表）。

    参数：
    - session：数据库会话
    - current_user：当前登录用户（依赖注入）

    返回值：
    - UserPublic：当前用户信息（含 scopes）
    """
    return await user_public(session=session, user=current_user)


# ======================== 用户管理路由（scope 判定） ========================
# 用户管理端点统一走 user:* scope 判定（超管天然拥有全部 scope，无需特判）。
# - 创建: user:create
# - 读取: user:read
# - 更新: user:update
# - 删除: user:admin 或 user:delete

@router.post(
    "/users/", response_model=UserPublic
)
async def create_user(
    *,
    session: SessionDep,
    user_in: UserCreate,
    _: Annotated[None, Depends(require_scope(UserScope.CREATE))],
) -> Any:
    """
    创建新用户。

    权限：拥有 user:create scope。

    参数：
    - session：数据库会话
    - user_in：用户创建 DTO（包含邮箱、密码等）

    返回值：
    - UserPublic：创建成功的用户信息

    业务流程：
    1. 检查邮箱是否已存在，存在则返回 409 错误
    2. 调用 repository create_user() 创建用户（密码自动哈希，默认分配 viewer 角色）
    """
    user = await service.create_user(session=session, user_in=user_in)

    return await user_public(session=session, user=user)


@router.get(
    "/users/",
    response_model=UsersPublic,
)
async def read_users(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Query()],
    _: Annotated[None, Depends(require_scope(UserScope.READ))],
) -> Any:
    """
    获取所有用户列表（分页）。

    权限：拥有 user:read scope（通过 dependencies 依赖注入强制）。

    参数：
    - session：数据库会话（依赖注入）
    - pagination：分页参数（page, page_size）

    返回值：
    - UsersPublic：包含 data（用户列表）、count（总数）、page（当前页）、page_size（每页大小）、total_pages（总页数）
    """
    users, count = await service.list_users(
        session=session,
        skip=pagination.offset,
        limit=pagination.limit,
    )

    return UsersPublic(
        data=await users_public(session=session, users=users),
        **paginated_fields(
            count=count,
            page=pagination.page,
            page_size=pagination.page_size,
        ),
    )


@router.get("/users/health-check/")
async def health_check() -> bool:
    return True


# ======================== 当前用户自助操作 ========================

@router.patch("/users/me", response_model=UserPublic)
async def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    更新当前用户自己的信息。

    权限：登录用户（自己的账户）

    参数：
    - session：数据库会话
    - user_in：用户更新 DTO（full_name、email 可选）
    - current_user：当前登录用户（依赖注入）

    返回值：
    - UserPublic：更新后的用户信息（含 scopes）

    业务逻辑：
    1. 若修改邮箱，检查新邮箱是否被其他用户占用
    2. 使用 model_dump(exclude_unset=True) 仅获取用户明确设置的字段
    3. 使用 sqlmodel_update() 合并更新
    4. 提交事务

    邮箱冲突处理：
    - 允许用户更新为自己的原邮箱
    - 若邮箱被其他用户占用，返回 409 冲突错误
    """
    current_user = await service.update_me(
        session=session, user=current_user, user_in=user_in
    )
    # 重新计算并附加权限 scope（角色可能未变化，但保证响应始终携带 scopes）
    return await user_public(session=session, user=current_user)


@router.patch("/users/me/password", response_model=Message)
async def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    修改当前用户自己的密码。

    权限：登录用户

    参数：
    - session：数据库会话
    - body：密码更新 DTO（current_password、new_password）
    - current_user：当前登录用户

    返回值：
    - Message：成功消息

    业务流程：
    1. 验证现有密码是否正确（调用 verify_password）
    2. 检查新密码是否与旧密码相同（防止无意义操作）
    3. 哈希新密码并保存到数据库
    4. 返回成功消息

    验证失败返回：
    - 400：密码错误
    - 400：新密码与旧密码相同
    """
    await service.update_password(session=session, user=current_user, body=body)
    return Message(message="Password updated successfully")


@router.get("/users/me", response_model=UserPublic)
async def read_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    获取当前登录用户的信息。

    权限：登录用户

    参数：
    - session：数据库会话（用于计算权限 scope）
    - current_user：当前登录用户（依赖注入）

    返回值：
    - UserPublic：当前用户信息（含 scopes 权限列表）

    说明：
    - scopes 由 get_user_scopes 实时计算（超管返回全部 scope）
    - 用于前端按 scope 控制导航和页面可见性
    """
    # 实时计算并附加当前用户的权限 scope 列表
    return await user_public(session=session, user=current_user)


@router.delete("/users/me", response_model=Message)
async def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    删除当前用户自己的账户。

    权限：登录用户

    参数：
    - session：数据库会话
    - current_user：当前登录用户

    返回值：
    - Message：删除成功消息

    业务逻辑：
    1. 检查当前用户是否为超管，超管不允许自删除（防止误操作导致系统无超管）
    2. 使用仓库函数删除用户记录
    3. 级联删除会由数据库约束自动处理（User.roles 关联表 userrole 外键为 CASCADE）

    异常：
    - 403：超管不允许删除自己
    """
    await service.delete_user(
        session=session, user=current_user, current_user=current_user
    )
    return Message(message="User deleted successfully")


# ======================== 公开路由（无需登录） ========================

@router.post("/users/signup", response_model=UserPublic)
async def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    用户自助注册（无需登录）。

    权限：公开

    参数：
    - session：数据库会话
    - user_in：用户注册 DTO（邮箱、密码、姓名）

    返回值：
    - UserPublic：创建的用户信息

    业务流程：
    1. 检查邮箱是否已存在
    2. 使用 model_validate 将 UserRegister DTO 转换为 UserCreate DTO
    3. 调用 repository.create_user() 创建用户

    异常：
    - 409：邮箱已被注册

    与 /users POST 的区别：
    - 此路由无需超管权限，任何人可注册
    - 此路由不发送邮件通知
    """
    user = await service.register_user(session=session, user_in=user_in)

    return await user_public(session=session, user=user)


# ======================== 更新用户（user:update 判定） ========================

@router.patch(
    "/users/{user_id}",
    response_model=UserPublic,
)
async def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
    _: Annotated[None, Depends(require_scope(UserScope.UPDATE))],
) -> Any:
    """
    更新指定用户信息（scope 判定）。

    权限：拥有 user:update scope。

    参数：
    - session：数据库会话
    - user_id：目标用户 UUID
    - user_in：用户更新 DTO（email、password、is_active、is_superuser 等可选）

    返回值：
    - UserPublic：更新后的用户信息

    业务流程：
    1. 查询目标用户是否存在
    2. 若修改邮箱，检查新邮箱唯一性（允许保持原邮箱）
    3. 调用 repository.update_user() 更新用户
    4. 返回更新后的用户

    异常：
    - 404：用户不存在
    - 409：新邮箱被其他用户占用
    - 403：无 user:update scope
    """
    user = await service.update_user(
        session=session, user_id=user_id, user_in=user_in
    )
    return await user_public(session=session, user=user)


# ======================== 删除用户（user:admin 判定） ========================

@router.delete("/users/{user_id}")
async def delete_user(
    session: SessionDep,
    current_user: CurrentUser,
    user_id: uuid.UUID,
    _: Annotated[None, Depends(require_any_scope(UserScope.ADMIN, UserScope.DELETE))],
) -> Message:
    """
    删除指定用户（scope 判定，而非超管判定）。

    权限：拥有 user:admin 或 user:delete scope（与用户管理删除按钮一致）。
    - 超管本身拥有全部 scope，天然满足此权限。
    - 普通拥有 user:delete scope 的角色（如 editor）也可删除用户。

    参数：
    - session：数据库会话
    - current_user：当前用户（用于禁止删除自己）
    - user_id：目标用户 UUID

    返回值：
    - Message：删除成功消息

    业务流程：
    1. 查询目标用户是否存在
    2. 防止删除自己（防止系统无管理员）
    3. 使用仓库函数删除用户记录（UserRole 关联由外键 CASCADE 自动清理）
    4. 返回成功消息

    异常：
    - 404：用户不存在
    - 403：不允许删除自己
    - 403：无 user:admin / user:delete scope

    注意：
    - User.roles 多对多关联的表 userrole 外键为 ondelete="CASCADE"，
      删除用户时数据库会自动清理其与角色的关联。
    """
    user = await service.get_user(session=session, user_id=user_id)
    await service.delete_user(
        session=session, user=user, current_user=current_user
    )
    return Message(message="User deleted successfully")


# ======================== 查询单个用户 ========================

@router.get("/users/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_scope(UserScope.READ))],
) -> Any:
    """
    获取指定用户信息。

    权限：拥有 user:read scope。

    参数：
    - user_id：目标用户 UUID
    - session：数据库会话
    - current_user：当前登录用户

    返回值：
    - UserPublic：用户信息

    业务流程：
    1. 查询指定用户
    2. 若不存在，返回 404

    异常：
    - 403：无 user:read scope
    - 404：用户不存在
    """
    user = await service.get_user(session=session, user_id=user_id)
    return await user_public(session=session, user=user)
