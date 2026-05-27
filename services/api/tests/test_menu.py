import uuid

import app.services.menu_service as menu_service

CREDS = {"email": "user@example.com", "password": "secret123"}
OTHER = {"email": "other@example.com", "password": "secret123"}


def _macros(kcal):
    return {"kcal": kcal, "protein_g": 30, "fat_g": 20, "carbs_g": 50}


def _sample_menu(day_kcal=2000):
    meal = {
        "type": "breakfast",
        "title": "Омлет",
        "ingredients": [{"name": "яйца", "amount": 150, "unit": "г"}],
        "steps": ["взбить", "пожарить"],
        "macros": _macros(day_kcal),
        "est_cost_rub": 90,
    }
    return {
        "days_count": 1,
        "total_per_day": _macros(day_kcal),
        "days": [{"day_index": 1, "totals": _macros(day_kcal), "meals": [meal]}],
    }


def _auth(client, creds):
    token = client.post("/auth/register", json=creds).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_generate_menu_success(client, monkeypatch):
    monkeypatch.setattr(menu_service, "generate_menu_json", lambda *_: _sample_menu())
    headers = _auth(client, CREDS)
    r = client.post("/menu/generate", headers=headers, json={"days_count": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["days_count"] == 1
    assert body["menu"]["days"][0]["meals"][0]["title"] == "Омлет"
    assert uuid.UUID(body["id"])


def test_generate_menu_scales_to_target(client, monkeypatch):
    monkeypatch.setattr(menu_service, "generate_menu_json", lambda *_: _sample_menu(day_kcal=1000))
    headers = _auth(client, CREDS)
    client.put("/profile", headers=headers, json={"target_kcal": 2000})
    r = client.post("/menu/generate", headers=headers, json={"days_count": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["adjusted"] is True
    assert body["menu"]["days"][0]["totals"]["kcal"] == 2000


def test_generate_menu_invalid_llm_output(client, monkeypatch):
    monkeypatch.setattr(menu_service, "generate_menu_json", lambda *_: {"garbage": True})
    headers = _auth(client, CREDS)
    r = client.post("/menu/generate", headers=headers, json={"days_count": 1})
    assert r.status_code == 502


def test_generate_menu_deepseek_error(client, monkeypatch):
    def _raise(*_):
        raise menu_service.DeepSeekError("boom")

    monkeypatch.setattr(menu_service, "generate_menu_json", _raise)
    headers = _auth(client, CREDS)
    r = client.post("/menu/generate", headers=headers, json={"days_count": 1})
    assert r.status_code == 502


def test_list_and_get_menu(client, monkeypatch):
    monkeypatch.setattr(menu_service, "generate_menu_json", lambda *_: _sample_menu())
    headers = _auth(client, CREDS)
    created = client.post("/menu/generate", headers=headers, json={"days_count": 1}).json()

    listing = client.get("/menu", headers=headers).json()
    assert len(listing) == 1
    assert listing[0]["id"] == created["id"]

    detail = client.get(f"/menu/{created['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["menu"]["days_count"] == 1


def test_menu_isolated_per_user(client, monkeypatch):
    monkeypatch.setattr(menu_service, "generate_menu_json", lambda *_: _sample_menu())
    h1 = _auth(client, CREDS)
    created = client.post("/menu/generate", headers=h1, json={"days_count": 1}).json()

    h2 = _auth(client, OTHER)
    assert client.get("/menu", headers=h2).json() == []
    assert client.get(f"/menu/{created['id']}", headers=h2).status_code == 404


def test_menu_requires_auth(client):
    assert client.post("/menu/generate", json={"days_count": 1}).status_code == 403
