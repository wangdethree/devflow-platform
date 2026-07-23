"""SQLAlchemy ORM 基础模型模块。

统一定义 ORM 模型基类和数据库约束命名规则，
供业务模型及 Alembic 数据迁移共同使用。
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


# 统一主键、外键、唯一约束和索引名称，
# 避免不同数据库自动生成不可预测的约束名称。
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """DevFlow ORM 模型统一基类。"""

    # 将命名规则应用到所有继承 Base 的数据库模型。
    metadata = MetaData(naming_convention=NAMING_CONVENTION)