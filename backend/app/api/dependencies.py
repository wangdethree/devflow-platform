"""认证用户与系统权限依赖。"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.database.dependencies import DatabaseSession
from app.models.user import User
from app.repositories.rbac_repository import RBACRepository
from app.repositories.user_repository import UserRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    session: DatabaseSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """解析 JWT 并加载当前有效用户。"""

    user_id = decode_access_token(token)
    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("当前账号不可用")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(permission_code: str):
    """创建系统权限依赖，供管理员接口声明式复用。"""

    async def permission_dependency(
        session: DatabaseSession,
        current_user: CurrentUser,
    ) -> User:
        permissions = await RBACRepository(session).get_permission_codes(
            current_user.id
        )
        if permission_code not in permissions:
            raise PermissionDeniedError("当前用户没有该系统权限")
        return current_user

    return permission_dependency
