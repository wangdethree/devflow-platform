"""Issue 评论 ORM 模型。"""

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Text, func

from app.database.base import Base


class Comment(Base):
    """项目成员围绕 Issue 发表的评论。"""

    __tablename__ = "comments"
    __table_args__ = {"comment": "Issue 评论表"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="评论主键")
    issue_id = Column(
        BigInteger,
        ForeignKey("issues.id"),
        nullable=False,
        comment="Issue 主键",
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        comment="评论用户",
    )
    content = Column(Text, nullable=False, comment="评论内容")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )
