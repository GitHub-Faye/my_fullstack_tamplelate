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
from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
    get_user_scopes,
)
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.core.schemas import Message, PaginationParams
from app.core.errors import (
    BusinessException,
    ErrorCode,
    raise_user_already_exists,
    raise_user_not_found,
    raise_permission_denied,
)

from app.domains.user import repository
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
    user = await repository.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise BusinessException(
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise BusinessException(
            code=ErrorCode.AUTH_INACTIVE_USER,
            detail="Inactive user"
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=create_access_token(
            user.id, expires_delta=access_token_expires
        )
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
    user_scopes = await get_user_scopes(session, current_user)
    return UserPublic.model_validate(current_user, update={"scopes": user_scopes})


# ======================== 超管-only 路由：创建用户 ========================

@router.post(
    "/users/", response_model=UserPublic
)
async def create_user(
    *,
    session: SessionDep,
    user_in: UserCreate,
    _: Annotated[None, Depends(get_current_active_superuser)],
) -> Any:
    """
    创建新用户（超管操作）。

    权限：超管-only

    参数：
    - session：数据库会话
    - user_in：用户创建 DTO（包含邮箱、密码等）

    返回值：
    - UserPublic：创建成功的用户信息

    业务流程：
    1. 检查邮箱是否已存在，存在则返回 409 错误
    2. 调用 repository create_user() 创建用户（密码自动哈希，默认分配 viewer 角色）
    """
    # 检查邮箱唯一性
    user = await repository.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise_user_already_exists("The user with this email already exists in the system.")

    # 创建用户（密码自动哈希）
    user = await repository.create_user(session=session, user_create=user_in)

    return user


@router.get(
    "/users/",
    response_model=UsersPublic,
)
async def read_users(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Query()],
    _: Annotated[None, Depends(get_current_active_superuser)],
) -> Any:
    """
    获取所有用户列表（分页）。

    权限：超管-only（通过 dependencies 依赖注入强制）

    参数：
    - session：数据库会话（依赖注入）
    - pagination：分页参数（page, page_size）

    返回值：
    - UsersPublic：包含 data（用户列表）、count（总数）、page（当前页）、page_size（每页大小）、total_pages（总页数）
    """
    # 使用仓库函数获取分页用户列表
    users, count = await repository.get_users(
        session=session,
        skip=pagination.offset,
        limit=pagination.limit
    )

    return UsersPublic(
        data=[UserPublic.model_validate(u) for u in users],
        count=count,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(count + pagination.page_size - 1) // pagination.page_size if count > 0 else 0,
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
    # 若修改邮箱，检查新邮箱是否被其他用户占用
    if user_in.email:
        existing_user = await repository.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise_user_already_exists("User with this email already exists")

    # 使用仓库函数更新用户信息
    current_user = await repository.update_user_me(
        session=session, db_user=current_user, user_in=user_in
    )
    # 重新计算并附加权限 scope（角色可能未变化，但保证响应始终携带 scopes）
    user_scopes = await get_user_scopes(session, current_user)
    return UserPublic.model_validate(current_user, update={"scopes": user_scopes})


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
    # 验证现有密码
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise BusinessException(
            code=ErrorCode.USER_INVALID_PASSWORD,
            detail="Incorrect password"
        )

    # 检查新密码是否与旧密码相同
    if body.current_password == body.new_password:
        raise BusinessException(
            code=ErrorCode.USER_PASSWORD_SAME_AS_OLD,
            detail="New password cannot be the same as the current one"
        )

    # 使用仓库函数更新密码
    await repository.update_password_me(
        session=session, db_user=current_user, new_password=body.new_password
    )
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
    user_scopes = await get_user_scopes(session, current_user)
    return UserPublic.model_validate(current_user, update={"scopes": user_scopes})


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
    3. 级联删除会由数据库约束自动处理（User.items 有 cascade_delete=True）

    异常：
    - 403：超管不允许删除自己
    """
    # 防止超管意外删除自己
    if current_user.is_superuser:
        raise BusinessException(
            code=ErrorCode.USER_CANNOT_DELETE_SELF,
            detail="Super users are not allowed to delete themselves"
        )
    # 使用仓库函数删除用户
    await repository.delete_user(session=session, db_user=current_user)
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
    # 检查邮箱唯一性
    user = await repository.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise_user_already_exists("The user with this email already exists in the system")

    # 将 UserRegister 转换为 UserCreate（Pydantic v2 用法）
    user_create = UserCreate.model_validate(user_in)
    user = await repository.create_user(session=session, user_create=user_create)

    return user


# ======================== 更新用户（超管操作） ========================

@router.patch(
    "/users/{user_id}",
    response_model=UserPublic,
)
async def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
    _: Annotated[None, Depends(get_current_active_superuser)],
) -> Any:
    """
    更新指定用户信息（超管操作）。

    权限：超管-only

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
    """
    # 查询目标用户
    user = await repository.get_user(session=session, user_id=user_id)
    if not user:
        raise_user_not_found("The user with this id does not exist in the system")

    # 若修改邮箱，检查新邮箱唯一性
    if user_in.email:
        existing_user = await repository.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise_user_already_exists("User with this email already exists")

    # 调用 CRUD 更新用户
    user = await repository.update_user(session=session, db_user=user, user_in=user_in)
    return user


# ======================== 删除用户（超管操作） ========================

@router.delete("/users/{user_id}")
async def delete_user(
    session: SessionDep,
    current_user: CurrentUser,
    user_id: uuid.UUID,
    _: Annotated[None, Depends(get_current_active_superuser)],
) -> Message:
    """
    删除指定用户（超管操作）。

    权限：超管-only

    参数：
    - session：数据库会话
    - current_user：当前超管用户（用于权限检查）
    - user_id：目标用户 UUID

    返回值：
    - Message：删除成功消息

    业务流程：
    1. 查询目标用户是否存在
    2. 防止超管删除自己（防止系统无超管）
    3. 使用仓库函数删除该用户的所有 Item（确保数据一致性）
    4. 使用仓库函数删除用户记录

    异常：
    - 404：用户不存在
    - 403：不允许删除自己

    注意：
    - 虽然 User.items 有 cascade_delete=True，但此处显式删除 Item
    - 这是为了确保数据库一致性和日志记录，避免某些场景下级联失败
    """
    # 查询目标用户
    user = await repository.get_user(session=session, user_id=user_id)
    if not user:
        raise_user_not_found()

    # 防止超管删除自己
    if user == current_user:
        raise BusinessException(
            code=ErrorCode.USER_CANNOT_DELETE_SELF,
            detail="Super users are not allowed to delete themselves"
        )

    # 使用仓库函数删除该用户的所有 Item（确保数据一致性）
    await repository.delete_user_items(session=session, user_id=user_id)

    # 使用仓库函数删除用户
    await repository.delete_user(session=session, db_user=user)
    return Message(message="User deleted successfully")


# ======================== 查询单个用户 ========================

@router.get("/users/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    获取指定用户信息。

    权限：
    - 用户可查看自己的信息
    - 超管可查看任何用户信息

    参数：
    - user_id：目标用户 UUID
    - session：数据库会话
    - current_user：当前登录用户

    返回值：
    - UserPublic：用户信息

    业务流程：
    1. 查询指定用户
    2. 若为自己，直接返回
    3. 若不是自己且当前用户非超管，返回 403 禁止访问
    4. 若用户不存在，返回 404

    异常：
    - 403：权限不足
    - 404：用户不存在
    """
    user = await repository.get_user(session=session, user_id=user_id)

    # 允许查看自己的信息
    if user == current_user:
        return user

    # 非超管不允许查看他人信息
    if not current_user.is_superuser:
        raise_permission_denied("The user doesn't have enough privileges")

    # 检查目标用户是否存在
    if user is None:
        raise_user_not_found()
    return user
