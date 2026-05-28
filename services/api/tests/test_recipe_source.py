from app.integrations.recipe_source import parse_jsonld_recipes

HTML = """
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Recipe",
  "name": "Куриный суп",
  "recipeIngredient": ["Курица 500 г", "Морковь 1 шт", "Лук 1 шт"],
  "recipeInstructions": [
    {"@type": "HowToStep", "text": "Отварить курицу"},
    {"@type": "HowToStep", "text": "Добавить овощи"}
  ],
  "recipeCuisine": "Русская",
  "keywords": "суп, обед",
  "nutrition": {
    "@type": "NutritionInformation",
    "calories": "240 ккал",
    "proteinContent": "20 g",
    "fatContent": "10 g",
    "carbohydrateContent": "15 g"
  }
}
</script>
</head><body></body></html>
"""

GRAPH_HTML = """
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
  {"@type":"WebPage","name":"page"},
  {"@type":["Recipe"],"name":"Овсянка","recipeIngredient":["Овсянка 100 г","Молоко 200 мл"]}
]}
</script>
"""


def test_parse_basic_recipe():
    recipes = parse_jsonld_recipes(HTML, source_url="http://example.com/r")
    assert len(recipes) == 1
    r = recipes[0]
    assert r.title == "Куриный суп"
    assert r.ingredients[0] == "Курица 500 г"
    assert r.steps == ["Отварить курицу", "Добавить овощи"]
    assert r.macros == {"kcal": 240.0, "protein_g": 20.0, "fat_g": 10.0, "carbs_g": 15.0}
    assert "Русская" in r.tags and "суп" in r.tags
    assert r.source_url == "http://example.com/r"
    assert len(r.content_hash) == 64


def test_parse_graph_recipe():
    recipes = parse_jsonld_recipes(GRAPH_HTML)
    assert len(recipes) == 1
    assert recipes[0].title == "Овсянка"
    assert recipes[0].macros is None


def test_parse_no_recipe():
    assert parse_jsonld_recipes("<html><body>nothing</body></html>") == []


def test_content_hash_stable():
    a = parse_jsonld_recipes(HTML)[0]
    b = parse_jsonld_recipes(HTML)[0]
    assert a.content_hash == b.content_hash
