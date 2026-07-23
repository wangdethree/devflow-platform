"""平台管理员用户管理接口。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import require_permission
from app.core.permissions import USER_MANAGE, USER_READ
from app.database.dependencies import DatabaseSession
from app.models.user import User
from app.schemas.user import (
    UserListResponse,
    UserResponse,
    UserStatusRequest,
)
from app.services.user_service import UserService


router = APIRouter(prefix="/admin", tags=["系统管理"])


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="管理员查询用户列表",
)
async def list_users(
    session: DatabaseSession,
    _: Annotated[User, Depends(require_permission(USER_READ))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> UserListResponse:
    items, total = await UserService(session).list_users(
        page=page,
        page_size=page_size,
    )
    return UserListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponse,
    summary="管理员启用或禁用用户",
)
async def update_user_status(
    user_id: int,
    payload: UserStatusRequest,
    session: DatabaseSession,
    _: Annotated[User, Depends(require_permission(USER_MANAGE))],
) -> UserResponse:
    return await UserService(session).set_active(user_id, payload.is_active)
