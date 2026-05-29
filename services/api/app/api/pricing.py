import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, SessionDep
from app.models.basket import BasketQuote
from app.schemas.pricing import PriceCompareIn, PriceCompareOut, ProviderBasket
from app.services.pricing import MenuNotFound, PricingService

router = APIRouter(prefix="/menu", tags=["pricing"])


def _to_out(quote: BasketQuote) -> PriceCompareOut:
    payload = quote.result or {}
    return PriceCompareOut(
        id=quote.id,
        menu_id=quote.menu_id,
        cheapest_provider=quote.cheapest_provider,
        proportional=bool(payload.get("proportional", False)),
        providers=[ProviderBasket.model_validate(p) for p in payload.get("providers", [])],
        created_at=quote.created_at,
    )


@router.post("/{menu_id}/prices", response_model=PriceCompareOut)
def compare_prices(
    menu_id: uuid.UUID,
    payload: PriceCompareIn,
    user: CurrentUser,
    session: SessionDep,
) -> PriceCompareOut:
    try:
        quote = PricingService(session).compare(
            user_id=user.id,
            menu_id=menu_id,
            provider_codes=payload.providers,
            proportional=payload.proportional,
        )
    except MenuNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_out(quote)


@router.get("/{menu_id}/prices", response_model=PriceCompareOut)
def get_prices(menu_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> PriceCompareOut:
    quote = PricingService(session).latest(user.id, menu_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No price quote")
    return _to_out(quote)
