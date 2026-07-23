"""当前用户站内通知接口。"""

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser
from app.database.dependencies import DatabaseSession
from app.schemas.notification import (
    MarkAllReadResponse,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification_service import NotificationService


router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("", response_model=NotificationListResponse, summary="查询通知")
async def list_notifications(
    current_user: CurrentUser,
    session: DatabaseSession,
    is_read: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> NotificationListResponse:
    items, total = await NotificationService(session).list_notifications(
        current_user,
        is_read=is_read,
        page=page,
        page_size=page_size,
    )
    return NotificationListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="查询未读通知数量",
)
async def unread_count(
    current_user: CurrentUser,
    session: DatabaseSession,
) -> UnreadCountResponse:
    count = await NotificationService(session).unread_count(current_user)
    return UnreadCountResponse(unread_count=count)


@router.patch(
    "/read-all",
    response_model=MarkAllReadResponse,
    summary="全部标记已读",
)
async def mark_all_read(
    current_user: CurrentUser,
    session: DatabaseSession,
) -> MarkAllReadResponse:
    count = await NotificationService(session).mark_all_read(current_user)
    return MarkAllReadResponse(updated_count=count)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="标记单条通知已读",
)
async def mark_read(
    notification_id: int,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> NotificationResponse:
    return await NotificationService(session).mark_read(
        notification_id,
        current_user,
    )
