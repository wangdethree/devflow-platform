"""角色权限关联 ORM 模型。

通过关联表实现系统角色与操作权限的多对多关系，
构成完整的 RBAC 权限模型。
"""

from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    UniqueConstraint,
)

from app.database.base import Base


class RolePermission(Base):
    """系统角色与权限的关联模型。"""

    __tablename__ = "role_permissions"

    __table_args__ = (
        # 同一个权限不能重复分配给同一角色。
        UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permissions_role_id_permission_id",
        ),
        {
            "comment": "角色权限关联表",
        },
    )

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="关联记录主键",
    )

    role_id = Column(
        BigInteger,
        ForeignKey("roles.id"),
        nullable=False,
        comment="角色主键",
    )

    permission_id = Column(
        BigInteger,
        ForeignKey("permissions.id"),
        nullable=False,
        comment="权限主键",
    )