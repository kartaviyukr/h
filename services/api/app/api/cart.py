import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, SessionDep
from app.models.cart import Cart
from app.schemas.cart import CartCreateIn, CartItemOut, CartOut
from app.services.cart import (
    CartError,
    CartService,
    MenuNotFound,
    ProviderNotFound,
    QuoteNotFound,
)

menu_router = APIRouter(prefix="/menu", tags=["cart"])
cart_router = APIRouter(prefix="/cart", tags=["cart"])


def _to_out(cart: Cart) -> CartOut:
    payload = cart.payload or {}
    return CartOut(
        id=cart.id,
        menu_id=cart.menu_id,
        basket_quote_id=cart.basket_quote_id,
        provider=cart.provider,
        total_rub=cart.total_rub,
        aggregated_url=cart.aggregated_url,
        items=[CartItemOut.model_validate(i) for i in payload.get("items", [])],
        unmatched=list(payload.get("unmatched", [])),
        created_at=cart.created_at,
    )


@menu_router.post("/{menu_id}/cart", response_model=CartOut)
def create_cart(
    menu_id: uuid.UUID, payload: CartCreateIn, user: CurrentUser, session: SessionDep
) -> CartOut:
    try:
        cart = CartService(session).create(
            user_id=user.id,
            menu_id=menu_id,
            provider=payload.provider,
            quote_id=payload.quote_id,
        )
    except MenuNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (QuoteNotFound, ProviderNotFound) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CartError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_out(cart)


@menu_router.get("/{menu_id}/cart", response_model=CartOut)
def get_menu_cart(menu_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> CartOut:
    cart = CartService(session).latest_for_menu(user.id, menu_id)
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No cart")
    return _to_out(cart)


@cart_router.get("/{cart_id}", response_model=CartOut)
def get_cart(cart_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> CartOut:
    cart = CartService(session).get(user.id, cart_id)
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    return _to_out(cart)
