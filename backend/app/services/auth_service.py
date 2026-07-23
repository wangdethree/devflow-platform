"""用户注册与登录业务服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.rbac_repository import RBACRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse


class AuthService:
    """编排注册、默认角色分配与 JWT 登录事务。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.rbac = RBACRepository(session)

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

    async def login(self, email: str, password: str) -> TokenResponse:
        """校验账号状态与密码并签发访问令牌。"""

        user = await self.users.get_by_email(email, include_deleted=True)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("邮箱或密码错误")
        if user.is_deleted or not user.is_active:
            raise AuthenticationError("账号已被禁用或删除")

        return TokenResponse(
            access_token=create_access_token(user.id),
            expires_in=settings.access_token_expire_minutes * 60,
        )
