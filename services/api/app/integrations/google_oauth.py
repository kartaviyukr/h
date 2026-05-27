from dataclasses import dataclass

import jwt
from jwt import PyJWKClient

from app.core.config import settings

_GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_VALID_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}

_jwk_client = PyJWKClient(_GOOGLE_CERTS_URL)


class GoogleTokenError(Exception):
    pass


@dataclass
class GoogleIdentity:
    sub: str
    email: str


def verify_google_id_token(id_token: str) -> GoogleIdentity:
    """Verify a Google ID token and return the identity.

    Raises GoogleTokenError on any validation failure.
    """
    if not settings.google_client_id:
        raise GoogleTokenError("Google client id is not configured")
    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.google_client_id,
        )
    except jwt.PyJWTError as exc:
        raise GoogleTokenError(str(exc)) from exc

    if claims.get("iss") not in _VALID_ISSUERS:
        raise GoogleTokenError("Invalid issuer")
    email = claims.get("email")
    sub = claims.get("sub")
    if not email or not sub:
        raise GoogleTokenError("Token missing email or sub")
    return GoogleIdentity(sub=sub, email=email.lower())
