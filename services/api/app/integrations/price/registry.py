import json
from decimal import Decimal
from pathlib import Path

from app.core.config import settings
from app.integrations.price.base import PriceProvider
from app.integrations.price.static import CatalogItem, StaticPriceProvider


def _load_catalog(path: str) -> list[StaticPriceProvider]:
    file_path = Path(path)
    if not file_path.is_absolute():
        # resolve relative to the API service root (parent of this app package)
        file_path = Path(__file__).resolve().parents[3] / path
    if not file_path.exists():
        return []
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    providers: list[StaticPriceProvider] = []
    for store in raw.get("providers", []):
        items = [
            CatalogItem(
                keywords=row["keywords"],
                name=row["name"],
                price_rub=Decimal(str(row["price_rub"])),
                package_size=float(row["package_size"]),
                base_unit=row["base_unit"],
                url=row.get("url"),
            )
            for row in store.get("catalog", [])
        ]
        providers.append(StaticPriceProvider(code=store["code"], name=store["name"], items=items))
    return providers


def get_providers() -> list[PriceProvider]:
    providers = _load_catalog(settings.price_catalog_path)
    if settings.price_providers:
        allowed = {c.strip() for c in settings.price_providers.split(",") if c.strip()}
        providers = [p for p in providers if p.code in allowed]
    return list(providers)
