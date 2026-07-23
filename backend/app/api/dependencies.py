"""认证用户与系统权限依赖。"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import TokenClaims, decode_access_token
from app.database.dependencies import DatabaseSession
from app.models.user import User
from app.repositories.auth_session_repository import AuthSessionRepository
from app.repositories.user_repository import UserRepository
from app.services.rbac_service import RBACService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@dataclass(frozen=True)
class AuthContext:
    """当前请求中已通过会话校验的身份。"""

    user: User
    claims: TokenClaims


async def get_auth_context(
    session: DatabaseSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> AuthContext:
    """解析 JWT，同时确认服务端会话未过期、未撤销。"""

    claims = decode_access_token(token)
    auth_session = await AuthSessionRepository(session).get(
        claims.session_id,
        claims.user_id,
    )
    now = datetime.now(UTC).replace(tzinfo=None)
    if (
        auth_session is None
        or auth_session.revoked_at is not None
        or auth_session.expires_at <= now
    ):
        raise AuthenticationError("登录会话不存在、已撤销或已过期")
    user = await UserRepository(session).get_by_id(claims.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("当前账号不可用")
    return AuthContext(user=user, claims=claims)


async def get_current_user(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
) -> User:
    return auth.user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAuth = Annotated[AuthContext, Depends(get_auth_context)]


def require_permission(permission_code: str):
    """创建系统权限依赖，供管理员接口声明式复用。"""

    async def permission_dependency(
        session: DatabaseSession,
        current_user: CurrentUser,
    ) -> User:
        permissions = await RBACService(session).get_permission_codes(
            current_user.id
        )
        if permission_code not in permissions:
            raise PermissionDeniedError("当前用户没有该系统权限")
        return current_user

    return permission_dependency
