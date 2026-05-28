import app.services.menu_service as menu_service
import app.services.recipe_index as recipe_index_module
from app.integrations.recipe_source import RecipeData
from app.services.recipe_index import RecipeIndexService
from tests.fakes import FakeEmbedder

CREDS = {"email": "user@example.com", "password": "secret123"}


def _macros(kcal):
    return {"kcal": kcal, "protein_g": 30, "fat_g": 20, "carbs_g": 50}


def _sample_menu():
    meal = {
        "type": "breakfast",
        "title": "Омлет",
        "ingredients": [{"name": "яйца", "amount": 150, "unit": "г"}],
        "steps": ["взбить"],
        "macros": _macros(2000),
        "est_cost_rub": 90,
    }
    return {
        "days_count": 1,
        "total_per_day": _macros(2000),
        "days": [{"day_index": 1, "totals": _macros(2000), "meals": [meal]}],
    }


def _auth(client):
    token = client.post("/auth/register", json=CREDS).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_retrieved_recipes_added_to_prompt(client, session, monkeypatch):
    RecipeIndexService(session, FakeEmbedder()).ingest(
        [RecipeData(title="Куриный суп", ingredients=["курица", "морковь"], steps=[], macros=None)]
    )
    monkeypatch.setattr(recipe_index_module, "get_embedder", FakeEmbedder)

    captured = {}

    def fake_llm(system_prompt, user_prompt):
        captured["user"] = user_prompt
        return _sample_menu()

    monkeypatch.setattr(menu_service, "generate_menu_json", fake_llm)

    headers = _auth(client)
    r = client.post("/menu/generate", headers=headers, json={"days_count": 1, "note": "курица"})
    assert r.status_code == 200
    assert "проверенные рецепты" in captured["user"]
    assert "Куриный суп" in captured["user"]


def test_empty_index_no_recipe_context(client, monkeypatch):
    captured = {}

    def fake_llm(system_prompt, user_prompt):
        captured["user"] = user_prompt
        return _sample_menu()

    monkeypatch.setattr(menu_service, "generate_menu_json", fake_llm)

    headers = _auth(client)
    r = client.post("/menu/generate", headers=headers, json={"days_count": 1})
    assert r.status_code == 200
    assert "проверенные рецепты" not in captured["user"]
