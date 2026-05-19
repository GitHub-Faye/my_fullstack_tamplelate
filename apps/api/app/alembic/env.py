"""
Alembic 迁移环境配置

此文件配置 Alembic 如何与数据库交互，包括：
1. 从 .env 文件加载数据库配置
2. 支持异步 PostgreSQL 数据库
3. 自动检测 SQLModel 模型变化
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# 添加项目根目录到 Python 路径
# 确保可以导入 app 模块
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# 导入所有模型以确保它们在 SQLModel.metadata 中注册
# 这行必须在导入 config 之前，确保模型已加载
from app.core.models import User, Item, Role, RoleScope, UserRole, BlogCategory, BlogPost, BlogComment  # noqa: F401

# 现在可以安全地导入配置
from app.core.config import get_settings

# Alembic Config 对象
config = context.config

# 加载日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标元数据 - SQLModel 会自动收集所有继承自 SQLModel 的表
# 这是 autogenerate 功能的关键
target_metadata = SQLModel.metadata

# 获取应用配置
settings = get_settings()


def get_database_url() -> str:
    """
    获取数据库连接 URL。
    
    优先顺序：
    1. 环境变量 DATABASE_URL
    2. 从 settings.SQLALCHEMY_DATABASE_URI 生成
    
    注意：Alembic 需要同步驱动，但 SQLAlchemy 1.4+ 支持 asyncpg
    我们使用 postgresql+asyncpg 驱动
    """
    # 从环境变量获取
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    
    # 从 settings 生成
    return settings.SQLALCHEMY_DATABASE_URI


def run_migrations_offline() -> None:
    """
    以离线模式运行迁移。
    
    离线模式不需要实际的数据库连接，只生成 SQL 脚本。
    适用于 CI/CD 环境或需要审查 SQL 的场景。
    """
    url = get_database_url()
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # 启用批量操作支持（PostgreSQL）
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    实际执行迁移的辅助函数。
    
    在异步上下文中运行同步的迁移操作。
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # 启用批量操作支持（PostgreSQL）
        render_as_batch=True,
        # 比较类型变化（如 VARCHAR(100) -> VARCHAR(200)）
        compare_type=True,
        # 比较服务器默认值
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    以在线模式运行迁移。
    
    在线模式需要实际的数据库连接，直接在数据库上执行迁移。
    这是开发和生产环境的默认模式。
    """
    # 获取数据库 URL
    database_url = get_database_url()
    
    # 创建异步引擎
    # 使用 NullPool 避免连接池问题
    connectable = create_async_engine(
        database_url,
        poolclass=pool.NullPool,
        echo=False,  # 迁移时关闭 SQL 回显
    )

    async with connectable.connect() as connection:
        # 在异步连接中运行同步的迁移
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# 根据运行模式执行迁移
if context.is_offline_mode():
    # 离线模式
    run_migrations_offline()
else:
    # 在线模式 - 使用 asyncio 运行异步函数
    asyncio.run(run_migrations_online())
