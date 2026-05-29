from decimal import Decimal

from app.integrations.price.static import CatalogItem, StaticPriceProvider
from app.services.pricing import _aggregate_ingredients, _basket_for_provider


def _provider_a():
    return StaticPriceProvider(
        code="a",
        name="A",
        items=[
            CatalogItem(["курица"], "Куриное филе", Decimal("350"), 1000, "g"),
            CatalogItem(["овсянка"], "Хлопья 500 г", Decimal("90"), 500, "g"),
        ],
    )


def _provider_b():
    return StaticPriceProvider(
        code="b",
        name="B",
        items=[
            CatalogItem(["курица"], "Филе 700 г", Decimal("290"), 700, "g"),
            CatalogItem(["овсянка"], "Хлопья 400 г", Decimal("75"), 400, "g"),
        ],
    )


def _menu_payload():
    return {
        "days": [
            {
                "meals": [
                    {
                        "ingredients": [
                            {"name": "Курица", "amount": 500, "unit": "г"},
                            {"name": "Овсянка", "amount": 100, "unit": "г"},
                        ]
                    },
                    {
                        "ingredients": [
                            {"name": "Курица", "amount": 300, "unit": "г"},
                            {"name": "Пучок укропа", "amount": 1, "unit": "пучок"},
                        ]
                    },
                ]
            }
        ]
    }


def test_aggregate_sums_same_ingredients():
    agg = _aggregate_ingredients(_menu_payload())
    by_name = {row["name"].lower(): row for row in agg}
    assert by_name["курица"]["base_amount"] == 800.0
    assert by_name["курица"]["group"] == "g"
    # Unknown unit is recorded but not priceable.
    assert by_name["пучок укропа"]["group"] == "?"


def test_basket_picks_packages_and_unmatched():
    agg = _aggregate_ingredients(_menu_payload())
    basket = _basket_for_provider(_provider_a(), agg, proportional=False)
    assert basket["matched_count"] == 2
    assert "Пучок укропа" in basket["unmatched"]
    chicken = next(i for i in basket["items"] if i["name"] == "Курица")
    # 800 г → 1 упаковка по 1000 г × 350 = 350
    assert chicken["packages"] == 1.0
    assert Decimal(chicken["cost_rub"]) == Decimal("350.00")
    oats = next(i for i in basket["items"] if i["name"] == "Овсянка")
    # 100 г → 1 упаковка по 500 г × 90 = 90
    assert Decimal(oats["cost_rub"]) == Decimal("90.00")
    assert Decimal(basket["total_rub"]) == Decimal("440.00")


def test_proportional_costs_are_lower_for_partial_use():
    agg = _aggregate_ingredients(_menu_payload())
    full = _basket_for_provider(_provider_a(), agg, proportional=False)
    prop = _basket_for_provider(_provider_a(), agg, proportional=True)
    assert Decimal(prop["total_rub"]) < Decimal(full["total_rub"])


def test_provider_comparison_picks_cheaper():
    agg = _aggregate_ingredients(_menu_payload())
    a = _basket_for_provider(_provider_a(), agg, proportional=False)
    b = _basket_for_provider(_provider_b(), agg, proportional=False)
    # B has 2 packages of 700 g chicken (580) + 1 oat (75) = 655
    # A: 350 + 90 = 440
    assert Decimal(a["total_rub"]) < Decimal(b["total_rub"])
