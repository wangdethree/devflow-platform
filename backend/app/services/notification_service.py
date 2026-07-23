"""当前用户站内通知业务服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.models.notification import Notification
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    """保证用户只能查询和操作自己的通知。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.notifications = NotificationRepository(session)

    async def list_notifications(
        self,
        user: User,
        *,
        is_read: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Notification], int]:
        """分页查询当前用户通知。"""

        return await self.notifications.list_for_user(
            user.id,
            is_read=is_read,
            page=page,
            page_size=page_size,
        )

    async def unread_count(self, user: User) -> int:
        """查询当前用户未读通知数量。"""

        return await self.notifications.unread_count(user.id)

    async def mark_read(
        self,
        notification_id: int,
        user: User,
    ) -> Notification:
        """标记一条所属通知已读。"""

        notification = await self.notifications.get(notification_id)
        if notification is None:
            raise ResourceNotFoundError("通知不存在")
        if notification.user_id != user.id:
            raise PermissionDeniedError("不能操作其他用户的通知")
        notification.is_read = True
        try:
            await self.session.commit()
            await self.session.refresh(notification)
            return notification
        except Exception:
            await self.session.rollback()
            raise

    async def mark_all_read(self, user: User) -> int:
        """批量标记当前用户全部未读通知。"""

        try:
            count = await self.notifications.mark_all_read(user.id)
            await self.session.commit()
            return count
        except Exception:
            await self.session.rollback()
            raise
