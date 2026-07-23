"""Issue Review 审核 ORM 模型。"""

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text, func, text

from app.database.base import Base


class Review(Base):
    """Issue 的一次审核请求与处理结果。"""

    __tablename__ = "reviews"
    __table_args__ = {"comment": "Issue Review 表"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="Review 主键")
    issue_id = Column(
        BigInteger,
        ForeignKey("issues.id"),
        nullable=False,
        comment="Issue 主键",
    )
    requester_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        comment="发起人",
    )
    reviewer_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        comment="审核人",
    )
    status = Column(
        String(30),
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
        comment="审核状态",
    )
    comment = Column(Text, nullable=True, comment="审核意见")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )
