"""ORM 模型公共字段模块。

集中定义多个业务模型重复使用的时间字段和软删除字段，
避免在各模型中重复声明相同结构。
"""

from sqlalchemy import Boolean, Column, DateTime, func, text


class TimestampMixin:
    """为业务模型提供创建时间和更新时间字段。"""

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),

        # 通过 ORM 更新记录时自动刷新修改时间。
        onupdate=func.now(),
        comment="更新时间",
    )


class SoftDeleteMixin:
    """为核心业务模型提供软删除标记。"""

    is_deleted = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
        comment="是否已删除",
    )