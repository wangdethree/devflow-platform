"""站内通知 ORM 模型。"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)

from app.database.base import Base


class Notification(Base):
    """用户站内通知及通用业务对象定位信息。"""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notifications_user_read", "user_id", "is_read"),
        {"comment": "站内通知表"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="通知主键")
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        comment="接收用户",
    )
    type = Column(String(50), nullable=False, comment="通知类型")
    target_type = Column(String(50), nullable=False, comment="关联对象类型")
    target_id = Column(BigInteger, nullable=False, comment="关联对象主键")
    content = Column(Text, nullable=False, comment="通知内容")
    is_read = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
        comment="是否已读",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )
