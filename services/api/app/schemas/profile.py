from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class Sex(StrEnum):
    male = "male"
    female = "female"


class ActivityLevel(StrEnum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    active = "active"
    very_active = "very_active"


class Goal(StrEnum):
    lose = "lose"
    maintain = "maintain"
    gain = "gain"


class BudgetPeriod(StrEnum):
    week = "week"
    month = "month"


class ProfileOut(BaseModel):
    display_name: str | None = None
    sex: Sex | None = None
    age: int | None = None
    height_cm: int | None = None
    weight_kg: Decimal | None = None
    activity_level: ActivityLevel | None = None
    goal: Goal | None = None
    target_kcal: int | None = None
    target_protein_g: int | None = None
    target_fat_g: int | None = None
    target_carbs_g: int | None = None
    allergies: list[str] = Field(default_factory=list)
    budget_rub: Decimal | None = None
    budget_period: BudgetPeriod | None = None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    """Partial update; only provided fields are applied."""

    display_name: str | None = None
    sex: Sex | None = None
    age: int | None = Field(default=None, ge=0, le=130)
    height_cm: int | None = Field(default=None, ge=0, le=300)
    weight_kg: Decimal | None = Field(default=None, ge=0, le=500)
    activity_level: ActivityLevel | None = None
    goal: Goal | None = None
    target_kcal: int | None = Field(default=None, ge=0, le=20000)
    target_protein_g: int | None = Field(default=None, ge=0, le=2000)
    target_fat_g: int | None = Field(default=None, ge=0, le=2000)
    target_carbs_g: int | None = Field(default=None, ge=0, le=2000)
    allergies: list[str] | None = None
    budget_rub: Decimal | None = Field(default=None, ge=0)
    budget_period: BudgetPeriod | None = None
