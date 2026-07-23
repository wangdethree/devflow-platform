"""为 Issue 增加乐观锁版本号

Revision ID: b741c6d2e903
Revises: 9d31f0b7a8c2
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b741c6d2e903"
down_revision: str | None = "9d31f0b7a8c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "issues",
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
            comment="乐观锁版本号",
        ),
    )


def downgrade() -> None:
    op.drop_column("issues", "version")
