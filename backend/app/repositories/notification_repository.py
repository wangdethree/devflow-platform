"""站内通知数据访问仓库。"""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    """封装通知写入、分页和已读状态更新。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: int,
        notification_type: str,
        target_type: str,
        target_id: int,
        content: str,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            target_type=target_type,
            target_id=target_id,
            content=content,
        )
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def list_for_user(
        self,
        user_id: int,
        *,
        is_read: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Notification], int]:
        filters = [Notification.user_id == user_id]
        if is_read is not None:
            filters.append(Notification.is_read.is_(is_read))
        total = await self.session.scalar(
            select(func.count(Notification.id)).where(*filters)
        )
        result = await self.session.execute(
            select(Notification)
            .where(*filters)
            .order_by(Notification.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars()), int(total or 0)

    async def get(self, notification_id: int) -> Notification | None:
        return (
            await self.session.execute(
                select(Notification).where(Notification.id == notification_id)
            )
        ).scalar_one_or_none()

    async def unread_count(self, user_id: int) -> int:
        count = await self.session.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return int(count or 0)

    async def mark_all_read(self, user_id: int) -> int:
        result = await self.session.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        return int(result.rowcount or 0)
