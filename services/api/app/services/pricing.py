import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.integrations.price.base import PriceProvider
from app.integrations.price.registry import get_providers
from app.models.basket import BasketQuote
from app.repositories.basket_repo import BasketRepository
from app.repositories.menu_repo import MenuRepository
from app.services.units import package_cost, to_base


class MenuNotFound(Exception):
    pass


def _aggregate_ingredients(menu_payload: dict) -> list[dict]:
    """Sum ingredient amounts across all meals/days, keyed by (name_lower, unit_group)."""
    bucket: dict[tuple[str, str], dict] = {}
    for day in menu_payload.get("days", []):
        for meal in day.get("meals", []):
            for ing in meal.get("ingredients", []):
                name = (ing.get("name") or "").strip()
                if not name:
                    continue
                amount = float(ing.get("amount") or 0)
                unit = ing.get("unit") or ""
                converted = to_base(amount, unit)
                if converted is None:
                    # unknown unit — record as unmatched without quantity
                    key = (name.lower(), "?")
                    bucket.setdefault(key, {"name": name, "base_amount": 0.0, "group": "?"})
                    continue
                base_amount, group = converted
                key = (name.lower(), group)
                if key not in bucket:
                    bucket[key] = {"name": name, "base_amount": 0.0, "group": group}
                bucket[key]["base_amount"] += base_amount
    return list(bucket.values())


def _basket_for_provider(
    provider: PriceProvider,
    aggregated: list[dict],
    proportional: bool,
) -> dict:
    items: list[dict] = []
    unmatched: list[str] = []
    total = Decimal("0.00")
    matched_count = 0

    for ing in aggregated:
        offer = provider.search(ing["name"]) if ing["group"] != "?" else None
        if offer is None:
            unmatched.append(ing["name"])
            items.append(
                {
                    "name": ing["name"],
                    "required_amount": ing["base_amount"],
                    "base_unit": ing["group"],
                    "matched": False,
                }
            )
            continue
        cost = package_cost(
            required_base=ing["base_amount"],
            group=ing["group"],
            offer_base_unit=offer.base_unit,
            package_size=offer.package_size,
            package_price=offer.price_rub,
            proportional=proportional,
        )
        if cost is None:
            unmatched.append(ing["name"])
            items.append(
                {
                    "name": ing["name"],
                    "required_amount": ing["base_amount"],
                    "base_unit": ing["group"],
                    "matched": False,
                }
            )
            continue
        cost_rub, packages = cost
        total += cost_rub
        matched_count += 1
        items.append(
            {
                "name": ing["name"],
                "required_amount": ing["base_amount"],
                "base_unit": ing["group"],
                "matched": True,
                "offer_name": offer.name,
                "packages": packages,
                "cost_rub": str(cost_rub),
                "url": offer.url,
            }
        )

    return {
        "provider": provider.code,
        "provider_name": provider.name,
        "total_rub": str(total.quantize(Decimal("0.01"))),
        "matched_count": matched_count,
        "unmatched": unmatched,
        "items": items,
    }


class PricingService:
    def __init__(self, session: Session, providers: list[PriceProvider] | None = None) -> None:
        self.session = session
        self.menus = MenuRepository(session)
        self.baskets = BasketRepository(session)
        self._providers = providers

    @property
    def providers(self) -> list[PriceProvider]:
        if self._providers is None:
            self._providers = get_providers()
        return self._providers

    def compare(
        self,
        user_id: uuid.UUID,
        menu_id: uuid.UUID,
        provider_codes: list[str] | None,
        proportional: bool,
    ) -> BasketQuote:
        menu = self.menus.get_for_user(user_id, menu_id)
        if menu is None:
            raise MenuNotFound("Menu not found")

        providers = self.providers
        if provider_codes:
            wanted = set(provider_codes)
            providers = [p for p in providers if p.code in wanted]

        aggregated = _aggregate_ingredients(menu.payload)
        baskets = [_basket_for_provider(p, aggregated, proportional) for p in providers]

        cheapest = None
        if baskets:
            cheapest_basket = min(baskets, key=lambda b: Decimal(b["total_rub"]))
            if cheapest_basket["matched_count"] > 0:
                cheapest = cheapest_basket["provider"]

        result = {"proportional": proportional, "providers": baskets}
        quote = self.baskets.create(
            menu_id=menu_id,
            user_id=user_id,
            cheapest_provider=cheapest,
            result=result,
        )
        self.session.commit()
        return quote

    def latest(self, user_id: uuid.UUID, menu_id: uuid.UUID) -> BasketQuote | None:
        if self.menus.get_for_user(user_id, menu_id) is None:
            return None
        return self.baskets.latest_for_menu(menu_id, user_id)
