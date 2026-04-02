from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select

from typing import AsyncGenerator

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.core.models import User

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


async def init_db():
    """初始化数据库（创建所有表，并添加默认超级用户）"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # 创建超级用户
    async with AsyncSessionLocal() as session:
        # 检查是否已存在该邮箱的用户
        result = await session.execute(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # 创建默认超级用户
            user = User(
                email=settings.FIRST_SUPERUSER,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                is_superuser=True,
                is_active=True,
                full_name="Admin",
            )
            session.add(user)
            await session.commit()
            print(f"✅ 默认超级用户已创建: {settings.FIRST_SUPERUSER}")
        else:
            print(f"ℹ️ 超级用户已存在: {settings.FIRST_SUPERUSER}")
