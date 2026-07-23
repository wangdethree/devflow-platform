"""基于 Redis 的可选登录限流。"""

import logging

from redis.exceptions import RedisError

from app.core.cache import redis_client
from app.core.config import settings
from app.core.exceptions import RateLimitError


logger = logging.getLogger(__name__)


async def check_login_rate_limit(identity: str) -> None:
    """同一客户端与邮箱每分钟最多尝试登录 10 次。"""

    if settings.environment == "test":
        return
    key = f"rate:login:{identity}"
    try:
        attempts = await redis_client.incr(key)
        if attempts == 1:
            await redis_client.expire(key, 60)
        if attempts > 10:
            raise RateLimitError("登录尝试过于频繁，请稍后再试")
    except RateLimitError:
        raise
    except (RedisError, OSError):
        logger.warning("Redis 不可用，跳过登录限流")
