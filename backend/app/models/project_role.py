"""项目级角色 ORM 模型。"""

from sqlalchemy import BigInteger, Column, String

from app.database.base import Base


class ProjectRole(Base):
    """项目成员在单个项目中的角色。"""

    __tablename__ = "project_roles"
    __table_args__ = {"comment": "项目角色表"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="角色主键")
    name = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="项目角色名称",
    )
    description = Column(String(255), nullable=True, comment="项目角色说明")
