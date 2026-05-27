import app.services.auth_service as auth_service
from app.integrations.google_oauth import GoogleIdentity

CREDS = {"email": "user@example.com", "password": "secret123"}


def test_register_returns_token(client):
    r = client.post("/auth/register", json=CREDS)
    assert r.status_code == 201
    assert r.json()["access_token"]
    assert r.json()["token_type"] == "bearer"


def test_register_duplicate_email_conflicts(client):
    client.post("/auth/register", json=CREDS)
    r = client.post("/auth/register", json=CREDS)
    assert r.status_code == 409


def test_register_short_password_rejected(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "short"})
    assert r.status_code == 422


def test_login_success(client):
    client.post("/auth/register", json=CREDS)
    r = client.post("/auth/login", json=CREDS)
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_wrong_password(client):
    client.post("/auth/register", json=CREDS)
    r = client.post("/auth/login", json={**CREDS, "password": "wrongpass1"})
    assert r.status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 403  # no Authorization header


def test_me_with_token(client):
    token = client.post("/auth/register", json=CREDS).json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == CREDS["email"]


def test_me_invalid_token(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_google_login_creates_user(client, monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "verify_google_id_token",
        lambda _t: GoogleIdentity(sub="g-123", email="g@example.com"),
    )
    r = client.post("/auth/google", json={"id_token": "fake"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "g@example.com"


def test_google_login_invalid_token(client, monkeypatch):
    def _raise(_t):
        raise auth_service.GoogleTokenError("bad")

    monkeypatch.setattr(auth_service, "verify_google_id_token", _raise)
    r = client.post("/auth/google", json={"id_token": "fake"})
    assert r.status_code == 401
