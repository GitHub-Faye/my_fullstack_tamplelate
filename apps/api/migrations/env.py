import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from sqlmodel import SQLModel

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -----------------------------------------------------------
# 导入所有模型，确保 SQLModel.metadata 包含所有 table 定义
# -----------------------------------------------------------
# 必须先导入模型，再赋值 target_metadata
from app.core.models import (
    Role, RoleScope, User, UserRole, Item, UserRoleType,
    Task, TaskStatus, TaskType, Bid, Attachment,
    DailyReport, StarPointRecord, ReportStage, JudgmentType,
    ClientResource, SystemRule, RuleCategory
)  # noqa: F401, E402

# SQLModel.metadata 是所有模型的公共元数据容器
target_metadata = SQLModel.metadata

# -----------------------------------------------------------
# 从应用配置中读取数据库连接 URL
# -----------------------------------------------------------
# 覆盖 alembic.ini 中的 sqlalchemy.url，改为从 .env 读取
from app.core.config import get_settings  # noqa: E402

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """在同步连接上执行迁移（由 run_migrations_online 中的 run_sync 调用）"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using async engine.

    使用异步引擎创建连接，然后通过 run_sync 调用同步迁移逻辑。
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async entry point)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
