import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart import Cart


class CartRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **fields) -> Cart:
        cart = Cart(**fields)
        self.session.add(cart)
        self.session.flush()
        return cart

    def get_for_user(self, user_id: uuid.UUID, cart_id: uuid.UUID) -> Cart | None:
        return self.session.scalar(
            select(Cart).where(Cart.id == cart_id, Cart.user_id == user_id)
        )

    def latest_for_menu(self, menu_id: uuid.UUID, user_id: uuid.UUID) -> Cart | None:
        return self.session.scalar(
            select(Cart)
            .where(Cart.menu_id == menu_id, Cart.user_id == user_id)
            .order_by(Cart.created_at.desc())
            .limit(1)
        )
