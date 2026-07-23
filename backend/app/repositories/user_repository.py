"""用户数据访问仓库。"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """封装用户查询和持久化操作，不处理业务权限与事务提交。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(
        self,
        user_id: int,
        *,
        include_deleted: bool = False,
    ) -> User | None:
        statement = select(User).where(User.id == user_id)
        if not include_deleted:
            statement = statement.where(User.is_deleted.is_(False))
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
        *,
        include_deleted: bool = False,
    ) -> User | None:
        statement = select(User).where(User.email == email.lower())
        if not include_deleted:
            statement = statement.where(User.is_deleted.is_(False))
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def create(
        self,
        *,
        username: str,
        email: str,
        password_hash: str,
    ) -> User:
        user = User(
            username=username,
            email=email.lower(),
            password_hash=password_hash,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def list_users(
        self,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[User], int]:
        filters = (User.is_deleted.is_(False),)
        total = await self.session.scalar(
            select(func.count(User.id)).where(*filters)
        )
        result = await self.session.execute(
            select(User)
            .where(*filters)
            .order_by(User.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars()), int(total or 0)
