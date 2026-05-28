import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

EMBEDDING_DIM = 384


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    ingredients: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'"))
    steps: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'"))
    macros: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default="{}")
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    content_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
