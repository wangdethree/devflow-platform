"""ORM 模型聚合模块。

统一导入全部业务模型，确保 SQLAlchemy 和 Alembic
能够从 Base.metadata 中发现完整的数据库表结构。
"""

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole


__all__ = [
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
]