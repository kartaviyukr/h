import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.integrations.deeplinks.registry import get_builder
from app.models.cart import Cart
from app.repositories.basket_repo import BasketRepository
from app.repositories.cart_repo import CartRepository
from app.repositories.menu_repo import MenuRepository


class CartError(Exception):
    """Raised for cart construction problems with a safe-to-expose message."""


class MenuNotFound(CartError):
    pass


class QuoteNotFound(CartError):
    pass


class ProviderNotFound(CartError):
    pass


class CartService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.menus = MenuRepository(session)
        self.baskets = BasketRepository(session)
        self.carts = CartRepository(session)

    def _resolve_quote(self, user_id, menu_id, quote_id):
        if quote_id is not None:
            quote = self.baskets.get_for_user(user_id, quote_id)
            if quote is None or quote.menu_id != menu_id:
                raise QuoteNotFound("Price quote not found for this menu")
            return quote
        quote = self.baskets.latest_for_menu(menu_id, user_id)
        if quote is None:
            raise QuoteNotFound("No price quote for this menu — run price comparison first")
        return quote

    def create(
        self,
        user_id: uuid.UUID,
        menu_id: uuid.UUID,
        provider: str | None,
        quote_id: uuid.UUID | None,
    ) -> Cart:
        if self.menus.get_for_user(user_id, menu_id) is None:
            raise MenuNotFound("Menu not found")

        quote = self._resolve_quote(user_id, menu_id, quote_id)
        result = quote.result or {}
        chosen = provider or quote.cheapest_provider
        if not chosen:
            raise ProviderNotFound("No provider could be selected (specify `provider`)")

        basket = next(
            (b for b in result.get("providers", []) if b["provider"] == chosen), None
        )
        if basket is None:
            raise ProviderNotFound(f"Provider '{chosen}' is not present in the quote")

        matched = [i for i in basket.get("items", []) if i.get("matched")]
        unmatched = list(basket.get("unmatched", []))
        total = sum((Decimal(i["cost_rub"]) for i in matched), Decimal("0.00"))

        link = get_builder(chosen).build(chosen, matched)

        payload = {
            "items": [
                {
                    "name": item["name"],
                    "offer_name": item["offer_name"],
                    "packages": item.get("packages"),
                    "cost_rub": item["cost_rub"],
                    "url": item.get("url"),
                }
                for item in matched
            ],
            "unmatched": unmatched,
        }

        cart = self.carts.create(
            user_id=user_id,
            menu_id=menu_id,
            basket_quote_id=quote.id,
            provider=chosen,
            total_rub=total.quantize(Decimal("0.01")),
            aggregated_url=link.aggregated_url,
            payload=payload,
        )
        self.session.commit()
        return cart

    def get(self, user_id: uuid.UUID, cart_id: uuid.UUID) -> Cart | None:
        return self.carts.get_for_user(user_id, cart_id)

    def latest_for_menu(self, user_id: uuid.UUID, menu_id: uuid.UUID) -> Cart | None:
        if self.menus.get_for_user(user_id, menu_id) is None:
            return None
        return self.carts.latest_for_menu(menu_id, user_id)
