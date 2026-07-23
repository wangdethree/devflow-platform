"""Issue 核心业务 ORM 模型。"""

from sqlalchemy import BigInteger, Column, ForeignKey, Index, Integer, String, Text, text

from app.database.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Issue(TimestampMixin, SoftDeleteMixin, Base):
    """项目中的 Bug、Feature 或 Task。"""

    __tablename__ = "issues"
    __table_args__ = (
        Index("idx_issues_project_id", "project_id"),
        Index("idx_issues_assignee_id", "assignee_id"),
        Index("idx_issues_status", "status"),
        Index("idx_issues_project_status", "project_id", "status"),
        {"comment": "Issue 核心业务表"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="Issue 主键")
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id"),
        nullable=False,
        comment="所属项目",
    )
    creator_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        comment="创建人",
    )
    assignee_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
        comment="负责人",
    )
    title = Column(String(200), nullable=False, comment="Issue 标题")
    description = Column(Text, nullable=True, comment="Issue 描述")
    type = Column(
        String(30),
        nullable=False,
        default="TASK",
        server_default=text("'TASK'"),
        comment="Issue 类型",
    )
    priority = Column(
        String(30),
        nullable=False,
        default="MEDIUM",
        server_default=text("'MEDIUM'"),
        comment="Issue 优先级",
    )
    status = Column(
        String(30),
        nullable=False,
        default="OPEN",
        server_default=text("'OPEN'"),
        comment="Issue 状态",
    )
    version = Column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="乐观锁版本号",
    )
