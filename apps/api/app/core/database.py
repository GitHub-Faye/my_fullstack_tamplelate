# 数据库管理分成了三个清晰的层次：

# Engine（连接池/底层驱动）
# Session Factory（会话工厂）
# Dependency / Context Provider（依赖注入或请求作用域的会话获取器）

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select, func

from typing import AsyncGenerator

from app.core.config import get_settings
from app.core.models import Role, RoleScope, User, UserRole
from app.core.scopes import DEFAULT_ROLE_SCOPES
from app.core.security import get_password_hash

settings = get_settings()

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,
    future=True,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖函数"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def sync_roles_scopes(session: AsyncSession) -> dict[str, list[str]]:
    """
    同步所有已存在角色的 scopes 到 DEFAULT_ROLE_SCOPES 的最新定义。
    """
    from app.core.scopes import DEFAULT_ROLE_SCOPES
    from app.core.models import Role, RoleScope

    result = await session.execute(select(Role))
    all_roles = result.scalars().all()

    changes: dict[str, list[str]] = {}

    for role in all_roles:
        if role.name not in DEFAULT_ROLE_SCOPES:
            continue

        scope_result = await session.execute(
            select(RoleScope.scope).where(RoleScope.role_id == role.id)
        )
        existing_scopes = {row[0] for row in scope_result.all()}

        expected_scopes = {s.value for s in DEFAULT_ROLE_SCOPES[role.name]}
        missing_scopes = expected_scopes - existing_scopes

        if missing_scopes:
            changes[role.name] = sorted(missing_scopes)
            for scope in missing_scopes:
                session.add(RoleScope(role_id=role.id, scope=scope))

    if changes:
        await session.commit()
        return changes

    return {}


async def init_roles_and_scopes(session: AsyncSession) -> None:
    """初始化默认角色和权限范围。"""
    for role_name, scopes in DEFAULT_ROLE_SCOPES.items():
        result = await session.execute(
            select(Role).where(Role.name == role_name)
        )
        existing_role = result.scalar_one_or_none()

        if existing_role:
            continue

        role = Role(name=role_name)
        session.add(role)
        await session.flush()

        for scope_value in scopes:
            role_scope = RoleScope(role_id=role.id, scope=scope_value)
            session.add(role_scope)

        print(f"Created role: {role_name} with scopes: {[s.value for s in scopes]}")

    await session.commit()


async def init_default_admin(session: AsyncSession) -> None:
    """如果系统中没有任何用户，创建一个默认 admin 用户。"""
    result = await session.execute(select(func.count()).select_from(User))
    user_count = result.scalar_one()

    if user_count > 0:
        print("Users already exist, skipping default admin creation.")
        return

    result = await session.execute(select(Role).where(Role.name == "admin"))
    admin_role = result.scalar_one_or_none()

    if not admin_role:
        print("Admin role not found, skipping default admin creation.")
        return

    admin_user = User(
        email="1@qq.com",
        hashed_password=get_password_hash("11111111"),
        full_name="Default Admin",
        is_superuser=True,
        is_active=True,
    )
    session.add(admin_user)
    await session.flush()

    user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
    session.add(user_role)

    await session.commit()
    print("Created default admin user (email: 1@qq.com, password: 11111111)")


async def init_db():
    """初始化数据库（创建所有表，并添加默认角色和权限）"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await init_roles_and_scopes(session)
        await init_default_admin(session)
        # 预置默认规则
        from app.domains.system_rule.repository import seed_default_rules
        await seed_default_rules(session=session)