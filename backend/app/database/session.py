"""异步数据库连接与会话管理模块。

负责创建 SQLAlchemy 异步引擎和会话工厂，
为 Repository 层提供统一的数据库访问入口。
"""

from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


# 使用 SQLAlchemy URL 对象构建连接地址，
# 避免数据库密码中的特殊字符导致 URL 解析异常。
DATABASE_URL = URL.create(
    drivername="mysql+asyncmy",
    username=settings.mysql_user,
    password=settings.mysql_password,
    host=settings.mysql_host,
    port=settings.mysql_port,
    database=settings.mysql_database,
)

# 创建全局异步数据库引擎。
engine_options: dict = {
    "echo": settings.debug,
    "pool_pre_ping": True,
    "pool_recycle": 1800,
}

# Pytest 会为测试创建独立事件循环；禁用连接复用可避免连接跨循环使用，
# 同时确保测试请求结束后立即归还数据库连接。
if settings.environment == "test":
    engine_options["poolclass"] = NullPool

engine = create_async_engine(DATABASE_URL, **engine_options)

# 创建异步会话工厂，每次调用都会生成独立的 AsyncSession。
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,

    # 提交事务后保留对象属性，避免再次访问时触发隐式查询。
    expire_on_commit=False,

    # 不在查询前自动刷新，由业务代码明确控制刷新时机。
    autoflush=False,
)
