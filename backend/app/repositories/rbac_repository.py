"""系统角色与权限数据访问仓库。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole


class RBACRepository:
    """封装 RBAC 角色、权限及关联关系查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_role_by_name(self, name: str) -> Role | None:
        return (
            await self.session.execute(select(Role).where(Role.name == name))
        ).scalar_one_or_none()

    async def assign_role(self, user_id: int, role_id: int) -> UserRole:
        relation = UserRole(user_id=user_id, role_id=role_id)
        self.session.add(relation)
        await self.session.flush()
        return relation

    async def get_permission_codes(self, user_id: int) -> set[str]:
        result = await self.session.execute(
            select(Permission.code)
            .join(
                RolePermission,
                RolePermission.permission_id == Permission.id,
            )
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return set(result.scalars())
