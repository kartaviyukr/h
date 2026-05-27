import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)

    # Антропометрия и цель
    sex: Mapped[str | None] = mapped_column(String, nullable=True)  # male/female
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    activity_level: Mapped[str | None] = mapped_column(String, nullable=True)
    goal: Mapped[str | None] = mapped_column(String, nullable=True)  # lose/maintain/gain

    # Целевые КБЖУ в день
    target_kcal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_protein_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_fat_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_carbs_g: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Аллергены и исключённые продукты (рус.)
    allergies: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )

    # Бюджет на продукты
    budget_rub: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_period: Mapped[str | None] = mapped_column(String, nullable=True)  # week/month

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="profile")  # noqa: F821
