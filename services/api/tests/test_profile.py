CREDS = {"email": "user@example.com", "password": "secret123"}
OTHER = {"email": "other@example.com", "password": "secret123"}


def _auth(client, creds):
    token = client.post("/auth/register", json=creds).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_profile_defaults_empty(client):
    headers = _auth(client, CREDS)
    r = client.get("/profile", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["allergies"] == []
    assert body["target_kcal"] is None


def test_profile_partial_update(client):
    headers = _auth(client, CREDS)
    r = client.put(
        "/profile",
        headers=headers,
        json={"target_kcal": 2000, "allergies": ["орехи", "лактоза"], "goal": "lose"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["target_kcal"] == 2000
    assert body["allergies"] == ["орехи", "лактоза"]
    assert body["goal"] == "lose"


def test_profile_requires_auth(client):
    assert client.get("/profile").status_code == 403


def test_profile_update_validation(client):
    headers = _auth(client, CREDS)
    r = client.put("/profile", headers=headers, json={"age": -5})
    assert r.status_code == 422


def test_profile_is_isolated_per_user(client):
    h1 = _auth(client, CREDS)
    client.put("/profile", headers=h1, json={"target_kcal": 1800})
    h2 = _auth(client, OTHER)
    r = client.get("/profile", headers=h2)
    assert r.json()["target_kcal"] is None
