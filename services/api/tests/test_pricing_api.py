from decimal import Decimal

import app.services.menu_service as menu_service
import app.services.pricing as pricing_service
from app.integrations.price.static import CatalogItem, StaticPriceProvider

CREDS = {"email": "user@example.com", "password": "secret123"}
OTHER = {"email": "other@example.com", "password": "secret123"}


def _macros(kcal):
    return {"kcal": kcal, "protein_g": 30, "fat_g": 20, "carbs_g": 50}


def _sample_menu():
    return {
        "days_count": 1,
        "total_per_day": _macros(2000),
        "days": [
            {
                "day_index": 1,
                "totals": _macros(2000),
                "meals": [
                    {
                        "type": "lunch",
                        "title": "Курица с гречкой",
                        "ingredients": [{"name": "Курица", "amount": 1500, "unit": "г"}],
                        "steps": ["варить"],
                        "macros": _macros(2000),
                        "est_cost_rub": 100,
                    }
                ],
            }
        ],
    }


def _providers():
    return [
        StaticPriceProvider(
            "a", "A", [CatalogItem(["курица"], "Куриное филе", Decimal("350"), 1000, "g")]
        ),
        StaticPriceProvider(
            "b", "B", [CatalogItem(["курица"], "Филе 700 г", Decimal("290"), 700, "g")]
        ),
    ]


def _auth(client, creds):
    return {
        "Authorization": "Bearer "
        + client.post("/auth/register", json=creds).json()["access_token"]
    }


def _create_menu(client, headers, monkeypatch):
    monkeypatch.setattr(menu_service, "generate_menu_json", lambda *_: _sample_menu())
    return client.post("/menu/generate", headers=headers, json={"days_count": 1}).json()["id"]


def test_compare_prices_returns_cheapest_and_saves(client, monkeypatch):
    monkeypatch.setattr(pricing_service, "get_providers", _providers)
    headers = _auth(client, CREDS)
    menu_id = _create_menu(client, headers, monkeypatch)

    r = client.post(f"/menu/{menu_id}/prices", headers=headers, json={})
    assert r.status_code == 200
    body = r.json()
    assert body["cheapest_provider"] == "a"
    assert len(body["providers"]) == 2

    r2 = client.get(f"/menu/{menu_id}/prices", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["id"] == body["id"]


def test_compare_prices_filters_providers(client, monkeypatch):
    monkeypatch.setattr(pricing_service, "get_providers", _providers)
    headers = _auth(client, CREDS)
    menu_id = _create_menu(client, headers, monkeypatch)

    r = client.post(f"/menu/{menu_id}/prices", headers=headers, json={"providers": ["b"]})
    assert r.status_code == 200
    body = r.json()
    assert [p["provider"] for p in body["providers"]] == ["b"]
    assert body["cheapest_provider"] == "b"


def test_compare_prices_missing_menu(client, monkeypatch):
    monkeypatch.setattr(pricing_service, "get_providers", _providers)
    headers = _auth(client, CREDS)
    r = client.post(
        "/menu/00000000-0000-0000-0000-000000000000/prices", headers=headers, json={}
    )
    assert r.status_code == 404


def test_prices_isolated_per_user(client, monkeypatch):
    monkeypatch.setattr(pricing_service, "get_providers", _providers)
    h1 = _auth(client, CREDS)
    menu_id = _create_menu(client, h1, monkeypatch)
    client.post(f"/menu/{menu_id}/prices", headers=h1, json={})

    h2 = _auth(client, OTHER)
    assert client.get(f"/menu/{menu_id}/prices", headers=h2).status_code == 404


def test_prices_require_auth(client):
    r = client.post(
        "/menu/00000000-0000-0000-0000-000000000000/prices", json={}
    )
    assert r.status_code == 403


def test_get_prices_404_when_none(client, monkeypatch):
    monkeypatch.setattr(pricing_service, "get_providers", _providers)
    headers = _auth(client, CREDS)
    menu_id = _create_menu(client, headers, monkeypatch)
    assert client.get(f"/menu/{menu_id}/prices", headers=headers).status_code == 404
