# 数据库管理分成了三个清晰的层次：

# Engine（连接池/底层驱动）
# Session Factory（会话工厂）
# Dependency / Context Provider（依赖注入或请求作用域的会话获取器）

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select, func
from sqlalchemy import event

from typing import AsyncGenerator

from app.core.config import get_settings
from app.core.models import Role, RoleScope, User, UserRole
from app.core.scopes import DEFAULT_ROLE_SCOPES
from app.core.security import get_password_hash

settings = get_settings()

# 创建异步引擎
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.DEBUG,  # 调试模式下打印 SQL
    poolclass=NullPool,  # 开发环境使用 NullPool，生产环境可改为 QueuePool
    future=True,
)


# SQLite 特殊处理：默认关闭外键约束，需在每次连接时显式开启（保证级联删除生效）
def _is_sqlite() -> bool:
    return settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite")


if _is_sqlite():

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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


async def init_roles_and_scopes(session: AsyncSession) -> None:
    """
    初始化默认角色和权限范围。

    创建以下默认角色：
    - viewer: 只读权限 (user:read)
    - editor: 读/写权限 (user:read, user:create, user:update, user:delete)
    - admin: 管理权限 (所有 user 权限 + 所有 role 权限)
    """
    for role_name, scopes in DEFAULT_ROLE_SCOPES.items():
        # 检查角色是否已存在
        result = await session.execute(
            select(Role).where(Role.name == role_name)
        )
        existing_role = result.scalar_one_or_none()
        
        if existing_role:
            # 角色已存在，跳过
            continue
        
        # 创建新角色
        role = Role(name=role_name)
        session.add(role)
        await session.flush()  # 获取 role.id
        
        # 创建角色的 scopes
        for scope_value in scopes:
            role_scope = RoleScope(role_id=role.id, scope=scope_value)
            session.add(role_scope)
        
        print(f"Created role: {role_name} with scopes: {[s.value for s in scopes]}")
    
    await session.commit()


async def init_default_admin(session: AsyncSession) -> None:
    """
    如果系统中没有任何用户，创建一个默认 admin 用户。
    
    默认管理员账号：
    - 邮箱: admin@admin.com
    - 密码: admin
    - 角色: admin（拥有所有 user 权限）+ superuser
    """
    # 检查是否已有用户
    result = await session.execute(select(func.count()).select_from(User))
    user_count = result.scalar_one()
    
    if user_count > 0:
        print("Users already exist, skipping default admin creation.")
        return
    
    # 查找 admin 角色
    result = await session.execute(select(Role).where(Role.name == "admin"))
    admin_role = result.scalar_one_or_none()
    
    if not admin_role:
        print("Admin role not found, skipping default admin creation.")
        return
    
    # 创建默认 admin 用户
    admin_user = User(
        email="1@qq.com",
        hashed_password=get_password_hash("11111111"),
        full_name="Default Admin",
        is_superuser=True,
        is_active=True,
    )
    session.add(admin_user)
    await session.flush()
    
    # 分配 admin 角色
    user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
    session.add(user_role)
    
    await session.commit()
    print("Created default admin user (email: admin@admin.com, password: admin)")


async def init_db():
    """初始化数据库（创建所有表，并添加默认角色和权限）"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # 初始化默认角色和 scopes
    async with AsyncSessionLocal() as session:
        await init_roles_and_scopes(session)
        await init_default_admin(session)
