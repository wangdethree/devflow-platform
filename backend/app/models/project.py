"""研发项目 ORM 模型。"""

from sqlalchemy import BigInteger, Column, ForeignKey, String, Text, text

from app.database.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Project(TimestampMixin, SoftDeleteMixin, Base):
    """项目基础信息及主负责人。"""

    __tablename__ = "projects"
    __table_args__ = {"comment": "研发项目表"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="项目主键")
    name = Column(String(100), nullable=False, comment="项目名称")
    description = Column(Text, nullable=True, comment="项目描述")
    status = Column(
        String(30),
        nullable=False,
        default="ACTIVE",
        server_default=text("'ACTIVE'"),
        comment="项目状态",
    )
    owner_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        comment="项目主负责人",
    )
