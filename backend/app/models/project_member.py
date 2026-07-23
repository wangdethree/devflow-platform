"""项目成员关系 ORM 模型。"""

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)

from app.database.base import Base


class ProjectMember(Base):
    """用户在项目中的成员与角色关系。"""

    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "user_id",
            name="uq_project_members_project_id_user_id",
        ),
        {"comment": "项目成员表"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="成员关系主键")
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id"),
        nullable=False,
        comment="项目主键",
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        comment="用户主键",
    )
    role_id = Column(
        BigInteger,
        ForeignKey("project_roles.id"),
        nullable=False,
        comment="项目角色主键",
    )
    joined_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="加入项目时间",
    )
