"""站内通知分页、未读数和响应 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    target_type: str
    target_id: int
    content: str
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    page: int
    page_size: int
    total: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class MarkAllReadResponse(BaseModel):
    updated_count: int
