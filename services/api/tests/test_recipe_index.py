from app.integrations.recipe_source import RecipeData
from app.services.recipe_index import RecipeIndexService
from tests.fakes import FakeEmbedder


def _recipe(title: str, ingredients: list[str]) -> RecipeData:
    return RecipeData(title=title, ingredients=ingredients, steps=[], macros=None)


def test_ingest_and_count(session):
    svc = RecipeIndexService(session, FakeEmbedder())
    n = svc.ingest(
        [
            _recipe("Куриный суп", ["курица"]),
            _recipe("Рыбные котлеты", ["рыба"]),
        ]
    )
    assert n == 2
    assert svc.count() == 2


def test_ingest_is_idempotent(session):
    svc = RecipeIndexService(session, FakeEmbedder())
    svc.ingest([_recipe("Куриный суп", ["курица"])])
    svc.ingest([_recipe("Куриный суп", ["курица"])])
    assert svc.count() == 1


def test_retrieve_orders_by_similarity(session):
    svc = RecipeIndexService(session, FakeEmbedder())
    svc.ingest(
        [
            _recipe("Куриный суп", ["курица"]),
            _recipe("Рыбные котлеты", ["рыба"]),
        ]
    )
    results = svc.retrieve("хочу блюдо где есть курица", k=2)
    assert results[0].title == "Куриный суп"


def test_retrieve_empty_index(session):
    svc = RecipeIndexService(session, FakeEmbedder())
    assert svc.retrieve("курица", k=5) == []
