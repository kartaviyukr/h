from dataclasses import dataclass
from decimal import Decimal

from app.integrations.price.base import ProductOffer


@dataclass
class CatalogItem:
    keywords: list[str]
    name: str
    price_rub: Decimal
    package_size: float
    base_unit: str
    url: str | None = None


class StaticPriceProvider:
    """In-memory catalog provider. Used for development, demos and tests."""

    def __init__(self, code: str, name: str, items: list[CatalogItem]) -> None:
        self.code = code
        self.name = name
        self._items = items

    def search(self, query: str) -> ProductOffer | None:
        q = query.lower()
        best: tuple[int, CatalogItem] | None = None
        for item in self._items:
            score = sum(1 for kw in item.keywords if kw.lower() in q)
            if score == 0:
                continue
            if best is None or score > best[0]:
                best = (score, item)
        if best is None:
            return None
        item = best[1]
        return ProductOffer(
            provider=self.code,
            name=item.name,
            price_rub=item.price_rub,
            package_size=item.package_size,
            base_unit=item.base_unit,
            url=item.url,
        )
