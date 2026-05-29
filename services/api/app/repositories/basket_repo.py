import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.basket import BasketQuote


class BasketRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        menu_id: uuid.UUID,
        user_id: uuid.UUID,
        cheapest_provider: str | None,
        result: dict,
    ) -> BasketQuote:
        quote = BasketQuote(
            menu_id=menu_id,
            user_id=user_id,
            cheapest_provider=cheapest_provider,
            result=result,
        )
        self.session.add(quote)
        self.session.flush()
        return quote

    def latest_for_menu(self, menu_id: uuid.UUID, user_id: uuid.UUID) -> BasketQuote | None:
        return self.session.scalar(
            select(BasketQuote)
            .where(BasketQuote.menu_id == menu_id, BasketQuote.user_id == user_id)
            .order_by(BasketQuote.created_at.desc())
            .limit(1)
        )
