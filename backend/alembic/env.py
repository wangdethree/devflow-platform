"""Alembic 数据库迁移环境配置。

统一加载 DevFlow 数据库配置和 ORM 元数据，
支持通过异步 MySQL 驱动执行数据库迁移。
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# 导入模型聚合模块，确保业务模型注册到 Base.metadata。
import app.models  # noqa: F401
from app.database.base import Base
from app.database.session import DATABASE_URL


# 获取当前 Alembic 配置对象。
config = context.config

# 使用 alembic.ini 中的日志配置。
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 自动迁移时用于对比 ORM 模型和数据库表结构。
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """以离线模式生成迁移 SQL。

    离线模式不直接连接数据库，主要用于输出可审查的 SQL 文件。
    """

    context.configure(
        url=DATABASE_URL.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """使用同步连接上下文执行 Alembic 迁移。"""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,

        # 检测字段类型变化，例如 VARCHAR 长度变化。
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """创建异步数据库连接并执行迁移。"""

    # 迁移任务使用独立引擎，并关闭连接池复用。
    # 每次 Alembic 命令结束后会立即释放数据库连接。
    connectable = create_async_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    try:
        async with connectable.connect() as connection:
            # Alembic 的迁移核心使用同步接口，
            # run_sync 负责在异步连接中安全调用同步迁移逻辑。
            await connection.run_sync(do_run_migrations)
    finally:
        # 无论迁移成功还是失败，都释放数据库引擎资源。
        await connectable.dispose()


def run_migrations_online() -> None:
    """以在线模式连接数据库并执行迁移。"""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()