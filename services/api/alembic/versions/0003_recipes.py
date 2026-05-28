"""recipes (RAG)

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-28

"""
from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "recipes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column(
            "ingredients", postgresql.JSONB(), server_default=sa.text("'[]'"), nullable=False
        ),
        sa.Column("steps", postgresql.JSONB(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("macros", postgresql.JSONB(), nullable=True),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash"),
    )
    op.create_index(
        "ix_recipes_embedding",
        "recipes",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.execute("COMMENT ON COLUMN recipes.embedding IS 'Вектор рецепта (pgvector)'")


def downgrade() -> None:
    op.drop_index("ix_recipes_embedding", table_name="recipes")
    op.drop_table("recipes")
