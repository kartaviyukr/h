import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CartCreateIn(BaseModel):
    provider: str | None = None
    quote_id: uuid.UUID | None = None


class CartItemOut(BaseModel):
    name: str
    offer_name: str
    packages: float | None = None
    cost_rub: Decimal
    url: str | None = None


class CartOut(BaseModel):
    id: uuid.UUID
    menu_id: uuid.UUID
    basket_quote_id: uuid.UUID | None
    provider: str
    total_rub: Decimal
    aggregated_url: str | None
    items: list[CartItemOut]
    unmatched: list[str]
    created_at: datetime
