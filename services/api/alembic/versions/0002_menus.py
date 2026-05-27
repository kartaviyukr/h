"""menus

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-27

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "menus",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("days_count", sa.Integer(), nullable=False),
        sa.Column("adjusted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "params",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_menus_user_id", "menus", ["user_id"])

    op.execute("COMMENT ON COLUMN menus.payload IS 'Сгенерированное меню (JSON)'")
    op.execute("COMMENT ON COLUMN menus.params IS 'Параметры и цели на момент генерации'")


def downgrade() -> None:
    op.drop_index("ix_menus_user_id", table_name="menus")
    op.drop_table("menus")
