import uuid

from sqlalchemy.orm import Session

from app.models.profile import Profile


class ProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, user_id: uuid.UUID) -> Profile | None:
        return self.session.get(Profile, user_id)

    def update(self, profile: Profile, fields: dict) -> Profile:
        for key, value in fields.items():
            setattr(profile, key, value)
        self.session.flush()
        return profile
