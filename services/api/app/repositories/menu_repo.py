import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.menu import Menu


class MenuRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        user_id: uuid.UUID,
        title: str,
        days_count: int,
        adjusted: bool,
        params: dict,
        payload: dict,
    ) -> Menu:
        menu = Menu(
            user_id=user_id,
            title=title,
            days_count=days_count,
            adjusted=adjusted,
            params=params,
            payload=payload,
        )
        self.session.add(menu)
        self.session.flush()
        return menu

    def list_for_user(self, user_id: uuid.UUID) -> Sequence[Menu]:
        return self.session.scalars(
            select(Menu).where(Menu.user_id == user_id).order_by(Menu.created_at.desc())
        ).all()

    def get_for_user(self, user_id: uuid.UUID, menu_id: uuid.UUID) -> Menu | None:
        return self.session.scalar(
            select(Menu).where(Menu.id == menu_id, Menu.user_id == user_id)
        )
