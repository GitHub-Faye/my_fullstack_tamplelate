"""
用户 API 路由模块

提供完整的用户管理 RESTful API 端点：
- 获取/创建/更新/删除用户
- 密码修改
- 用户自助注册/个人信息更新
- 权限控制（超管-only 端点）
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import col, delete, func, select


from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import get_settings
from app.core.security import get_password_hash, verify_password
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
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)


from app.core.models import Item, User
  

from app.tasks.user_tasks import process_user_signup_task

settings = get_settings()
# ======================== APIRouter 创建 ========================
router = APIRouter()


# ======================== 超管-only 路由：获取所有用户 ========================

@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
async def read_users(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Query()],
) -> Any:
    """
    获取所有用户列表（分页）。
    
    权限：超管-only（通过 dependencies 依赖注入强制）
    
    参数：
    - session：数据库会话（依赖注入）
    - pagination：分页参数（page, page_size）
    
    返回值：
    - UsersPublic：包含 data（用户列表）、count（总数）、page（当前页）、page_size（每页大小）、total_pages（总页数）
    
    查询语句：
    1. 使用 func.count() 获取用户总数
    2. 使用 order_by(col(User.created_at).desc()) 按创建时间降序排列
    3. 使用 offset/limit 分页
    """
    # 获取用户总数
    count_statement = select(func.count()).select_from(User)
    result = await session.execute(count_statement)
    count = result.scalar_one()

    # 获取分页的用户列表（按创建时间倒序）
    statement = (
        select(User)
        .order_by(User.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    result = await session.execute(statement)
    users = result.scalars().all()

    return UsersPublic(
        data=users,
        count=count,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(count + pagination.page_size - 1) // pagination.page_size if count > 0 else 0,
    )


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
async def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    创建新用户（超管操作）。
    
    权限：超管-only
    
    参数：
    - session：数据库会话
    - user_in：用户创建 DTO（包含邮箱、密码等）
    
    返回值：
    - UserPublic：创建成功的用户信息
    
    业务流程：
    1. 检查邮箱是否已存在，存在则返回 400 错误
    2. 调用 repository create_user() 创建用户（密码自动哈希）
    3. 若启用邮件服务，生成新账户邮件并发送
    
    邮件通知：
    - 包含临时密码（用于提醒用户首次修改）
    - 若邮件发送失败不影响用户创建成功
    """
    # 检查邮箱唯一性
    user = await repository.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise_user_already_exists("The user with this email already exists in the system.")

    # 创建用户（密码自动哈希）
    user = await repository.create_user(session=session, user_create=user_in)

    return user


# ======================== 当前用户自助操作 ========================

@router.patch("/me", response_model=UserPublic)
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
    - UserPublic：更新后的用户信息
    
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
    
    # 仅序列化用户明确设置的字段（exclude_unset=True）
    user_data = user_in.model_dump(exclude_unset=True)
    # 使用 sqlmodel_update() 合并数据
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
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
    
    # 哈希新密码并保存
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    await session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
async def read_user_me(current_user: CurrentUser) -> Any:
    """
    获取当前登录用户的信息。
    
    权限：登录用户
    
    参数：
    - current_user：当前登录用户（依赖注入）
    
    返回值：
    - UserPublic：当前用户信息
    
    说明：
    - 无需数据库查询，直接返回依赖注入的 current_user
    - 用于前端检查登录状态、显示用户信息
    """
    return current_user


@router.delete("/me", response_model=Message)
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
    2. 删除用户记录
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
    await session.delete(current_user)
    await session.commit()
    return Message(message="User deleted successfully")


# ======================== 公开路由（无需登录） ========================

@router.post("/signup", response_model=UserPublic)
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
    - 400：邮箱已被注册
    
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
    
    # 异步处理用户注册后续任务
    process_user_signup_task.delay(
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name
    )
    
    return user


# ======================== 查询单个用户 ========================

@router.get("/{user_id}", response_model=UserPublic)
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
    user = await session.get(User, user_id)
    
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


# ======================== 更新用户（超管操作） ========================

@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
async def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
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
    db_user = await session.get(User, user_id)
    if not db_user:
        raise_user_not_found("The user with this id does not exist in the system")
    
    # 若修改邮箱，检查新邮箱唯一性
    if user_in.email:
        existing_user = await repository.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise_user_already_exists("User with this email already exists")

    # 调用 CRUD 更新用户
    db_user = await repository.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


# ======================== 删除用户（超管操作） ========================

@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
async def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
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
    3. 手动删除该用户的所有 Item（因为关联表可能有特殊处理）
    4. 删除用户记录（级联会自动删除 items）
    5. 提交事务
    
    异常：
    - 404：用户不存在
    - 403：不允许删除自己
    
    注意：
    - 虽然 User.items 有 cascade_delete=True，但此处显式删除 Item
    - 这是为了确保数据库一致性和日志记录，避免某些场景下级联失败
    """
    # 查询目标用户
    user = await session.get(User, user_id)
    if not user:
        raise_user_not_found()
    
    # 防止超管删除自己
    if user == current_user:
        raise BusinessException(
            code=ErrorCode.USER_CANNOT_DELETE_SELF,
            detail="Super users are not allowed to delete themselves"
        )
    
    # 显式删除该用户的所有 Item（确保数据一致性）
    statement = delete(Item).where(Item.owner_id == user_id)
    await session.execute(statement)
    
    # 删除用户
    await session.delete(user)
    await session.commit()
    return Message(message="User deleted successfully")


@router.get("/health-check/")
async def health_check() -> bool:
    return True