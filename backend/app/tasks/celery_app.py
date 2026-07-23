"""DevFlow Celery 应用配置。"""

from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "devflow",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.notifications"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)
