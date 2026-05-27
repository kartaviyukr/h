import uuid

from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.repositories.profile_repo import ProfileRepository
from app.schemas.profile import ProfileUpdate


class ProfileService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.profiles = ProfileRepository(session)

    def get(self, user_id: uuid.UUID) -> Profile | None:
        return self.profiles.get(user_id)

    def update(self, user_id: uuid.UUID, data: ProfileUpdate) -> Profile | None:
        profile = self.profiles.get(user_id)
        if profile is None:
            return None
        fields = data.model_dump(exclude_unset=True)
        # Store enum values as plain strings.
        fields = {k: (v.value if hasattr(v, "value") else v) for k, v in fields.items()}
        self.profiles.update(profile, fields)
        self.session.commit()
        return profile
