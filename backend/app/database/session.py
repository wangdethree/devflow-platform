"""异步数据库连接与会话管理模块。

负责创建 SQLAlchemy 异步引擎和会话工厂，
为 Repository 层提供统一的数据库访问入口。
"""

from sqlalchemy.engine import URL
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
engine = create_async_engine(
    DATABASE_URL,

    # 开发调试时输出 SQL，生产环境应关闭。
    echo=settings.debug,

    # 从连接池取出连接前验证其可用性。
    pool_pre_ping=True,

    # 定期回收连接，降低 MySQL 主动断开空闲连接的影响。
    pool_recycle=1800,
)

# 创建异步会话工厂，每次调用都会生成独立的 AsyncSession。
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,

    # 提交事务后保留对象属性，避免再次访问时触发隐式查询。
    expire_on_commit=False,

    # 不在查询前自动刷新，由业务代码明确控制刷新时机。
    autoflush=False,
)