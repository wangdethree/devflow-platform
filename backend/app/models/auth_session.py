"""用户登录会话 ORM 模型。"""

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)

from app.database.base import Base


class AuthSession(Base):
    """保存 Refresh Token 轮换状态，并支持主动撤销设备会话。"""

    __tablename__ = "auth_sessions"
    __table_args__ = (
        Index("idx_auth_sessions_user_id", "user_id"),
        Index("idx_auth_sessions_expires_at", "expires_at"),
        {"comment": "用户认证会话表"},
    )

    id = Column(String(36), primary_key=True, comment="会话 UUID")
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        comment="所属用户",
    )
    refresh_token_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        comment="当前 Refresh Token SHA-256 摘要",
    )
    rotation_count = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="令牌轮换次数",
    )
    ip_address = Column(String(45), nullable=True, comment="登录 IP")
    user_agent = Column(String(255), nullable=True, comment="登录客户端")
    expires_at = Column(DateTime, nullable=False, comment="会话过期时间")
    last_used_at = Column(DateTime, nullable=True, comment="最后轮换时间")
    revoked_at = Column(DateTime, nullable=True, comment="撤销时间")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )

