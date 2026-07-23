"""数据库通知的可重试 Redis 事件发布任务。"""

import asyncio
import json
import logging

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.database.session import AsyncSessionLocal, engine
from app.repositories.notification_repository import NotificationRepository
from app.tasks.celery_app import celery_app


logger = logging.getLogger(__name__)


async def _load_notification(notification_id: int) -> dict | None:
    try:
        async with AsyncSessionLocal() as session:
            notification = await NotificationRepository(session).get(
                notification_id
            )
            if notification is None:
                return None
            return {
                "id": notification.id,
                "user_id": notification.user_id,
                "type": notification.type,
                "target_type": notification.target_type,
                "target_id": notification.target_id,
                "content": notification.content,
            }
    finally:
        # 查询与连接池释放必须处于同一事件循环。
        await engine.dispose()


@celery_app.task(
    bind=True,
    autoretry_for=(RedisError, OSError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def dispatch_notification(self, notification_id: int) -> bool:
    """读取已提交通知并发布到用户专属 Redis Channel。"""

    payload = asyncio.run(_load_notification(notification_id))
    if payload is None:
        logger.warning("通知不存在 notification_id=%s", notification_id)
        return False

    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        client.publish(
            f"devflow:notifications:{payload['user_id']}",
            json.dumps(payload, ensure_ascii=False),
        )
    finally:
        client.close()
    return True


def enqueue_notification_delivery(notification_id: int) -> None:
    """尽力提交异步分发任务，Broker 不可用不影响已落库通知。"""

    if settings.environment == "test":
        return
    try:
        dispatch_notification.delay(notification_id)
    except Exception:
        logger.warning(
            "通知异步分发入队失败 notification_id=%s",
            notification_id,
            exc_info=True,
        )
