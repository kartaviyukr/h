from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.integrations.google_oauth import GoogleTokenError, verify_google_id_token
from app.models.user import User
from app.repositories.user_repo import UserRepository


class AuthError(Exception):
    """Raised for auth failures; message is safe to expose."""


class EmailAlreadyExists(AuthError):
    pass


class InvalidCredentials(AuthError):
    pass


class InvalidGoogleToken(AuthError):
    pass


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def register(self, email: str, password: str) -> str:
        email = email.lower()
        if self.users.get_by_email(email):
            raise EmailAlreadyExists("Email already registered")
        user = self.users.create(email=email, password_hash=hash_password(password))
        self.session.commit()
        return create_access_token(str(user.id))

    def login(self, email: str, password: str) -> str:
        user = self.users.get_by_email(email.lower())
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            raise InvalidCredentials("Invalid email or password")
        return create_access_token(str(user.id))

    def login_with_google(self, id_token: str) -> str:
        try:
            identity = verify_google_id_token(id_token)
        except GoogleTokenError as exc:
            raise InvalidGoogleToken(str(exc)) from exc

        user = self.users.get_by_google_sub(identity.sub)
        if not user:
            user = self._link_or_create_google_user(identity.email, identity.sub)
        self.session.commit()
        return create_access_token(str(user.id))

    def _link_or_create_google_user(self, email: str, google_sub: str) -> User:
        existing = self.users.get_by_email(email)
        if existing:
            existing.google_sub = google_sub
            self.session.flush()
            return existing
        return self.users.create(email=email, google_sub=google_sub)
