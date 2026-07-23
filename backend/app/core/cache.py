"""可选 Redis 缓存客户端。

Redis 异常只会降低缓存与限流能力，不会阻断 MySQL 核心业务。
"""

import json
import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings


logger = logging.getLogger(__name__)

redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=0.2,
    socket_timeout=0.2,
)


async def get_json(key: str):
    """读取 JSON 缓存，Redis 不可用时返回 None。"""

    if settings.environment == "test":
        return None
    try:
        value = await redis_client.get(key)
        return json.loads(value) if value is not None else None
    except (RedisError, OSError, ValueError):
        logger.warning("Redis 缓存读取失败 key=%s", key)
        return None


async def set_json(key: str, value, *, ttl: int) -> None:
    """写入带过期时间的 JSON 缓存，失败时静默降级。"""

    if settings.environment == "test":
        return
    try:
        await redis_client.set(key, json.dumps(value), ex=ttl)
    except (RedisError, OSError):
        logger.warning("Redis 缓存写入失败 key=%s", key)


async def close_redis() -> None:
    """应用退出时释放 Redis 连接池。"""

    await redis_client.aclose()
