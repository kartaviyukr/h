from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class ProductOffer:
    provider: str
    name: str
    price_rub: Decimal
    package_size: float  # expressed in base_unit
    base_unit: str  # "g" | "ml" | "pcs"
    url: str | None = None


class PriceProvider(Protocol):
    code: str
    name: str

    def search(self, query: str) -> ProductOffer | None:
        """Return the best matching offer for `query`, or None if nothing matched."""
        ...
