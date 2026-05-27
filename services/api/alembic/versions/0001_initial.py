"""initial: users and profiles

Revision ID: 0001
Revises:
Create Date: 2026-05-27

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("google_sub", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_sub"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("sex", sa.String(), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("height_cm", sa.Integer(), nullable=True),
        sa.Column("weight_kg", sa.Numeric(5, 2), nullable=True),
        sa.Column("activity_level", sa.String(), nullable=True),
        sa.Column("goal", sa.String(), nullable=True),
        sa.Column("target_kcal", sa.Integer(), nullable=True),
        sa.Column("target_protein_g", sa.Integer(), nullable=True),
        sa.Column("target_fat_g", sa.Integer(), nullable=True),
        sa.Column("target_carbs_g", sa.Integer(), nullable=True),
        sa.Column(
            "allergies",
            postgresql.ARRAY(sa.String()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("budget_rub", sa.Numeric(10, 2), nullable=True),
        sa.Column("budget_period", sa.String(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.execute("COMMENT ON COLUMN profiles.allergies IS 'Аллергены и исключённые продукты'")
    op.execute("COMMENT ON COLUMN profiles.goal IS 'Цель: похудение/поддержание/набор'")
    op.execute("COMMENT ON COLUMN profiles.budget_rub IS 'Бюджет на продукты, рубли'")


def downgrade() -> None:
    op.drop_table("profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
