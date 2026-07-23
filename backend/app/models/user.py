"""用户 ORM 模型。

保存用户身份信息、登录凭证和账号状态。
"""

from sqlalchemy import BigInteger, Boolean, Column, String, text

from app.database.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class User(TimestampMixin, SoftDeleteMixin, Base):
    """系统用户模型。"""

    __tablename__ = "users"

    __table_args__ = {
        "comment": "系统用户表",
    }

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="用户主键",
    )

    username = Column(
        String(50),
        nullable=False,
        comment="用户名",
    )

    email = Column(
        String(100),
        nullable=False,
        unique=True,
        comment="用户邮箱",
    )

    password_hash = Column(
        String(255),
        nullable=False,
        comment="密码哈希值",
    )

    avatar = Column(
        String(255),
        nullable=True,
        comment="头像地址",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
        comment="账号是否启用",
    )