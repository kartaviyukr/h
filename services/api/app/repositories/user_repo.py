import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.models.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))

    def get_by_google_sub(self, google_sub: str) -> User | None:
        return self.session.scalar(select(User).where(User.google_sub == google_sub))

    def create(
        self,
        email: str,
        password_hash: str | None = None,
        google_sub: str | None = None,
    ) -> User:
        user = User(email=email, password_hash=password_hash, google_sub=google_sub)
        user.profile = Profile()
        self.session.add(user)
        self.session.flush()
        return user
