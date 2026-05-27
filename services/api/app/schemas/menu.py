import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class MealType(StrEnum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"


class Macros(BaseModel):
    kcal: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)


class Ingredient(BaseModel):
    name: str
    amount: float = Field(ge=0)
    unit: str


class Meal(BaseModel):
    type: MealType
    title: str
    ingredients: list[Ingredient]
    steps: list[str] = Field(default_factory=list)
    macros: Macros
    est_cost_rub: Decimal | None = None


class MenuDay(BaseModel):
    day_index: int = Field(ge=1)
    totals: Macros
    meals: list[Meal]


class MenuOut(BaseModel):
    """Contract for the LLM output and the stored menu payload."""

    days_count: int = Field(ge=1, le=7)
    total_per_day: Macros
    days: list[MenuDay]


# ---- API request / response ----


class MenuGenerateIn(BaseModel):
    days_count: int = Field(default=3, ge=1, le=7)
    include_snacks: bool = True
    note: str | None = Field(default=None, max_length=500)


class MenuDetail(BaseModel):
    id: uuid.UUID
    title: str
    days_count: int
    adjusted: bool
    created_at: datetime
    menu: MenuOut


class MenuListItem(BaseModel):
    id: uuid.UUID
    title: str
    days_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
