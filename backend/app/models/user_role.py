"""用户角色关联 ORM 模型。

通过关联表实现用户与系统角色的多对多关系。
"""

from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    UniqueConstraint,
)

from app.database.base import Base


class UserRole(Base):
    """用户与系统角色的关联模型。"""

    __tablename__ = "user_roles"

    __table_args__ = (
        # 同一用户不能重复拥有同一个角色。
        UniqueConstraint(
            "user_id",
            "role_id",
            name="uq_user_roles_user_id_role_id",
        ),
        {
            "comment": "用户角色关联表",
        },
    )

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="关联记录主键",
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        comment="用户主键",
    )

    role_id = Column(
        BigInteger,
        ForeignKey("roles.id"),
        nullable=False,
        comment="角色主键",
    )