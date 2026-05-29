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
            "a",
            "A",
            [
                CatalogItem(
                    ["курица"], "Куриное филе", Decimal("350"), 1000, "g",
                    url="https://a.example/p/chicken",
                )
            ],
        ),
        StaticPriceProvider(
            "b",
            "B",
            [
                CatalogItem(
                    ["курица"], "Филе 700 г", Decimal("290"), 700, "g",
                    url="https://b.example/p/chicken",
                )
            ],
        ),
    ]


def _auth(client, creds):
    return {
        "Authorization": "Bearer "
        + client.post("/auth/register", json=creds).json()["access_token"]
    }


def _setup_menu_with_quote(client, headers, monkeypatch):
    monkeypatch.setattr(menu_service, "generate_menu_json", lambda *_: _sample_menu())
    monkeypatch.setattr(pricing_service, "get_providers", _providers)
    menu_id = client.post("/menu/generate", headers=headers, json={"days_count": 1}).json()["id"]
    client.post(f"/menu/{menu_id}/prices", headers=headers, json={}).json()
    return menu_id


def test_create_cart_uses_cheapest_by_default(client, monkeypatch):
    headers = _auth(client, CREDS)
    menu_id = _setup_menu_with_quote(client, headers, monkeypatch)

    r = client.post(f"/menu/{menu_id}/cart", headers=headers, json={})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "a"  # 1500g chicken: a=2×350=700 < b=3×290=870
    assert body["aggregated_url"] is None
    assert body["items"][0]["url"] == "https://a.example/p/chicken"
    assert Decimal(body["total_rub"]) == Decimal("700.00")


def test_create_cart_explicit_provider(client, monkeypatch):
    headers = _auth(client, CREDS)
    menu_id = _setup_menu_with_quote(client, headers, monkeypatch)

    r = client.post(f"/menu/{menu_id}/cart", headers=headers, json={"provider": "b"})
    assert r.status_code == 200
    assert r.json()["provider"] == "b"
    assert r.json()["items"][0]["url"] == "https://b.example/p/chicken"


def test_create_cart_unknown_provider(client, monkeypatch):
    headers = _auth(client, CREDS)
    menu_id = _setup_menu_with_quote(client, headers, monkeypatch)
    r = client.post(f"/menu/{menu_id}/cart", headers=headers, json={"provider": "zz"})
    assert r.status_code == 400


def test_create_cart_without_quote(client, monkeypatch):
    monkeypatch.setattr(menu_service, "generate_menu_json", lambda *_: _sample_menu())
    headers = _auth(client, CREDS)
    menu_id = client.post("/menu/generate", headers=headers, json={"days_count": 1}).json()["id"]
    r = client.post(f"/menu/{menu_id}/cart", headers=headers, json={})
    assert r.status_code == 400


def test_create_cart_menu_not_found(client):
    headers = _auth(client, CREDS)
    r = client.post(
        "/menu/00000000-0000-0000-0000-000000000000/cart", headers=headers, json={}
    )
    assert r.status_code == 404


def test_get_cart_endpoints_and_isolation(client, monkeypatch):
    h1 = _auth(client, CREDS)
    menu_id = _setup_menu_with_quote(client, h1, monkeypatch)
    cart_id = client.post(f"/menu/{menu_id}/cart", headers=h1, json={}).json()["id"]

    assert client.get(f"/menu/{menu_id}/cart", headers=h1).status_code == 200
    assert client.get(f"/cart/{cart_id}", headers=h1).status_code == 200

    h2 = _auth(client, OTHER)
    assert client.get(f"/cart/{cart_id}", headers=h2).status_code == 404
    assert client.get(f"/menu/{menu_id}/cart", headers=h2).status_code == 404


def test_cart_requires_auth(client):
    assert (
        client.post(
            "/menu/00000000-0000-0000-0000-000000000000/cart", json={}
        ).status_code
        == 403
    )
