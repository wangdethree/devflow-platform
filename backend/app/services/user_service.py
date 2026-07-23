"""用户资料与平台级管理服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ResourceNotFoundError
from app.models.user import User
from app.repositories.rbac_repository import RBACRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdateRequest


class UserService:
    """处理资料更新、权限读取和管理员用户管理。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.rbac = RBACRepository(session)

    async def update_profile(
        self,
        user: User,
        payload: UserUpdateRequest,
    ) -> User:
        """更新当前用户资料并保证邮箱唯一。"""

        data = payload.model_dump(exclude_unset=True)
        if "email" in data:
            existing = await self.users.get_by_email(
                str(data["email"]),
                include_deleted=True,
            )
            if existing is not None and existing.id != user.id:
                raise ConflictError("该邮箱已被其他用户使用")
            data["email"] = str(data["email"]).lower()

        for field, value in data.items():
            setattr(user, field, value)

        try:
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except Exception:
            await self.session.rollback()
            raise

    async def list_users(
        self,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[User], int]:
        """返回未删除用户分页列表。"""

        return await self.users.list_users(page=page, page_size=page_size)

    async def set_active(self, user_id: int, is_active: bool) -> User:
        """启用或禁用目标用户。"""

        user = await self.users.get_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError("用户不存在")
        user.is_active = is_active
        try:
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except Exception:
            await self.session.rollback()
            raise
