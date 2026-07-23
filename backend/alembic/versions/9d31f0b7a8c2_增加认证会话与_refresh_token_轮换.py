"""增加认证会话与 Refresh Token 轮换

Revision ID: 9d31f0b7a8c2
Revises: 759adf3f87a8
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "9d31f0b7a8c2"
down_revision: str | None = "759adf3f87a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(length=36), nullable=False, comment="会话 UUID"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="所属用户"),
        sa.Column(
            "refresh_token_hash",
            sa.String(length=64),
            nullable=False,
            comment="当前 Refresh Token SHA-256 摘要",
        ),
        sa.Column(
            "rotation_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="令牌轮换次数",
        ),
        sa.Column("ip_address", sa.String(length=45), nullable=True, comment="登录 IP"),
        sa.Column(
            "user_agent",
            sa.String(length=255),
            nullable=True,
            comment="登录客户端",
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False, comment="会话过期时间"),
        sa.Column("last_used_at", sa.DateTime(), nullable=True, comment="最后轮换时间"),
        sa.Column("revoked_at", sa.DateTime(), nullable=True, comment="撤销时间"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_auth_sessions_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_sessions")),
        sa.UniqueConstraint(
            "refresh_token_hash",
            name=op.f("uq_auth_sessions_refresh_token_hash"),
        ),
        comment="用户认证会话表",
    )
    op.create_index(
        "idx_auth_sessions_expires_at",
        "auth_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "idx_auth_sessions_user_id",
        "auth_sessions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("auth_sessions")
