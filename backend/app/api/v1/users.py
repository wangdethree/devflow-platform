"""当前用户资料与权限接口。"""

from fastapi import APIRouter

from app.api.dependencies import CurrentUser
from app.database.dependencies import DatabaseSession
from app.schemas.user import (
    PermissionListResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.services.user_service import UserService
from app.services.rbac_service import RBACService


router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", response_model=UserResponse, summary="获取个人资料")
async def get_profile(current_user: CurrentUser) -> UserResponse:
    """返回当前登录用户的公开资料。"""

    return current_user


@router.patch("/me", response_model=UserResponse, summary="修改个人资料")
async def update_profile(
    payload: UserUpdateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> UserResponse:
    """修改当前登录用户的用户名、邮箱或头像。"""

    return await UserService(session).update_profile(current_user, payload)


@router.get(
    "/me/permissions",
    response_model=PermissionListResponse,
    summary="查询当前用户权限",
)
async def get_my_permissions(
    current_user: CurrentUser,
    session: DatabaseSession,
) -> PermissionListResponse:
    permissions = await RBACService(session).get_permission_codes(
        current_user.id
    )
    return PermissionListResponse(permissions=sorted(permissions))
