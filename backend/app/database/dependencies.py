"""数据库依赖注入模块。

为每个 HTTP 请求创建独立数据库会话，
并在请求结束后统一释放数据库资源。
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """提供请求级异步数据库会话。

    请求处理成功时由业务层决定是否提交事务；
    请求处理异常时回滚当前事务。
    """

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            # 防止异常请求留下未完成事务。
            await session.rollback()
            raise


# 统一数据库会话依赖声明，减少 API 层的重复代码。
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]