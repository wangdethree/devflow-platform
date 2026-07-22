"""SQLAlchemy ORM 基础模型模块。

所有数据库模型统一继承 Base，
便于 SQLAlchemy 和 Alembic 收集模型元数据。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """DevFlow ORM 模型统一基类."""

    pass