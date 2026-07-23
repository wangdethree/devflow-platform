"""系统角色 ORM 模型。

系统角色用于聚合操作权限，例如 Admin 和 User。
"""

from sqlalchemy import BigInteger, Column, String

from app.database.base import Base


class Role(Base):
    """系统级角色模型。"""

    __tablename__ = "roles"

    __table_args__ = {
        "comment": "系统角色表",
    }

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="角色主键",
    )

    name = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="角色名称",
    )

    description = Column(
        String(255),
        nullable=True,
        comment="角色说明",
    )
