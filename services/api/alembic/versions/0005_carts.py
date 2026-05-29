"""carts (Phase 6)

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-29

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "carts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("menu_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("basket_quote_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("total_rub", sa.Numeric(12, 2), nullable=False),
        sa.Column("aggregated_url", sa.String(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["menu_id"], ["menus.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["basket_quote_id"], ["basket_quotes.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_carts_menu_created", "carts", ["menu_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_carts_menu_created", table_name="carts")
    op.drop_table("carts")
