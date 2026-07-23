"""带 Redis 降级缓存的系统权限服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_json, set_json
from app.repositories.rbac_repository import RBACRepository


class RBACService:
    """缓存稳定的角色权限编码，Redis 异常时回源 MySQL。"""

    def __init__(self, session: AsyncSession) -> None:
        self.rbac = RBACRepository(session)

    async def get_permission_codes(self, user_id: int) -> set[str]:
        """读取用户权限，缓存有效期为 5 分钟。"""

        key = f"rbac:user:{user_id}:permissions"
        cached = await get_json(key)
        if isinstance(cached, list):
            return set(cached)
        permissions = await self.rbac.get_permission_codes(user_id)
        await set_json(key, sorted(permissions), ttl=300)
        return permissions
