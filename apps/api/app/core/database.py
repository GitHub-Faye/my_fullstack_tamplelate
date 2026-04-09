from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select

from typing import AsyncGenerator

from app.core.config import get_settings
from app.core.models import Role, RoleScope
from app.core.scopes import DEFAULT_ROLE_SCOPES

settings = get_settings()

# 创建异步引擎
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.DEBUG,  # 调试模式下打印 SQL
    poolclass=NullPool,  # 开发环境使用 NullPool，生产环境可改为 QueuePool
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


async def init_roles_and_scopes(session: AsyncSession) -> None:
    """
    初始化默认角色和权限范围。
    
    创建以下默认角色：
    - viewer: 只读权限 (item:read)
    - editor: 完全权限 (item:read, item:create, item:update, item:delete)
    - admin: 管理权限 (所有 item 权限)
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


async def init_db():
    """初始化数据库（创建所有表，并添加默认角色和权限）"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # 初始化默认角色和 scopes
    async with AsyncSessionLocal() as session:
        await init_roles_and_scopes(session)
