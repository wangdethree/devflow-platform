"""系统权限 ORM 模型。

使用唯一权限编码表示用户可以执行的系统操作。
"""

from sqlalchemy import BigInteger, Column, String

from app.database.base import Base


class Permission(Base):
    """系统操作权限模型。"""

    __tablename__ = "permissions"

    __table_args__ = {
        "comment": "系统权限表",
    }

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="权限主键",
    )

    code = Column(
        String(100),
        nullable=False,
        unique=True,
        comment="权限唯一编码",
    )

    description = Column(
        String(255),
        nullable=True,
        comment="权限说明",
    )