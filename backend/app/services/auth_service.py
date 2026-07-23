"""用户注册与登录业务服务。"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    TokenClaims,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories.auth_session_repository import AuthSessionRepository
from app.repositories.rbac_repository import RBACRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse


class AuthService:
    """编排注册、默认角色分配与 JWT 登录事务。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.rbac = RBACRepository(session)
        self.auth_sessions = AuthSessionRepository(session)

    async def register(self, payload: RegisterRequest) -> User:
        """创建用户并在同一事务中分配默认 User 系统角色。"""

        if await self.users.get_by_email(payload.email, include_deleted=True):
            raise ConflictError("该邮箱已注册")

        default_role = await self.rbac.get_role_by_name("User")
        if default_role is None:
            raise ConflictError("系统基础角色尚未初始化，请先执行 seed 命令")

        try:
            user = await self.users.create(
                username=payload.username.strip(),
                email=payload.email,
                password_hash=hash_password(payload.password),
            )
            await self.rbac.assign_role(user.id, default_role.id)
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except Exception:
            await self.session.rollback()
            raise

    def _token_response(
        self,
        user_id: int,
        session_id: str,
        refresh_token: str,
    ) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id, session_id),
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            refresh_expires_in=settings.refresh_token_expire_days * 86400,
        )

    async def login(
        self,
        email: str,
        password: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """校验账号状态，创建持久化设备会话并签发令牌对。"""

        user = await self.users.get_by_email(email, include_deleted=True)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("邮箱或密码错误")
        if user.is_deleted or not user.is_active:
            raise AuthenticationError("账号已被禁用或删除")

        session_id = str(uuid4())
        refresh_token = create_refresh_token(user.id, session_id)
        expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(
            days=settings.refresh_token_expire_days
        )
        try:
            await self.auth_sessions.create(
                session_id=session_id,
                user_id=user.id,
                refresh_token_hash=hash_token(refresh_token),
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=(user_agent or "")[:255] or None,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return self._token_response(user.id, session_id, refresh_token)

    async def refresh(self, raw_refresh_token: str) -> TokenResponse:
        """轮换 Refresh Token；检测到旧令牌重放时立即撤销会话。"""

        claims = decode_refresh_token(raw_refresh_token)
        now = datetime.now(UTC).replace(tzinfo=None)
        auth_session = await self.auth_sessions.get(
            claims.session_id,
            claims.user_id,
            for_update=True,
        )
        if (
            auth_session is None
            or auth_session.revoked_at is not None
            or auth_session.expires_at <= now
        ):
            await self.session.rollback()
            raise AuthenticationError("登录会话不存在、已撤销或已过期")

        if auth_session.refresh_token_hash != hash_token(raw_refresh_token):
            auth_session.revoked_at = now
            await self.session.commit()
            raise AuthenticationError("检测到 Refresh Token 重放，会话已撤销")

        user = await self.users.get_by_id(claims.user_id)
        if user is None or not user.is_active:
            auth_session.revoked_at = now
            await self.session.commit()
            raise AuthenticationError("当前账号不可用")

        new_refresh_token = create_refresh_token(user.id, auth_session.id)
        auth_session.refresh_token_hash = hash_token(new_refresh_token)
        auth_session.rotation_count += 1
        auth_session.last_used_at = now
        auth_session.expires_at = now + timedelta(
            days=settings.refresh_token_expire_days
        )
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return self._token_response(user.id, auth_session.id, new_refresh_token)

    async def revoke_session(self, claims: TokenClaims) -> int:
        """撤销当前 Access Token 所属会话。"""

        revoked = await self.auth_sessions.revoke(
            claims.session_id,
            claims.user_id,
            datetime.now(UTC).replace(tzinfo=None),
        )
        await self.session.commit()
        return int(revoked)

    async def revoke_all_sessions(self, user_id: int) -> int:
        """撤销用户全部设备会话。"""

        count = await self.auth_sessions.revoke_all(
            user_id,
            datetime.now(UTC).replace(tzinfo=None),
        )
        await self.session.commit()
        return count
