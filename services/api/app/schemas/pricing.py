import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PriceCompareIn(BaseModel):
    providers: list[str] | None = None  # default: all configured
    proportional: bool = False


class BasketItem(BaseModel):
    name: str
    required_amount: float
    base_unit: str
    matched: bool
    offer_name: str | None = None
    packages: float | None = None
    cost_rub: Decimal | None = None
    url: str | None = None


class ProviderBasket(BaseModel):
    provider: str
    provider_name: str
    total_rub: Decimal
    matched_count: int
    unmatched: list[str] = Field(default_factory=list)
    items: list[BasketItem]


class PriceCompareOut(BaseModel):
    id: uuid.UUID
    menu_id: uuid.UUID
    cheapest_provider: str | None
    proportional: bool
    providers: list[ProviderBasket]
    created_at: datetime
