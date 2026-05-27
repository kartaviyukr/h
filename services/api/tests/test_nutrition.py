from app.models.profile import Profile
from app.schemas.menu import Ingredient, Macros, Meal, MenuDay, MenuOut


def _menu(day_kcal: float) -> MenuOut:
    meal = Meal(
        type="breakfast",
        title="Каша",
        ingredients=[Ingredient(name="овсянка", amount=100, unit="г")],
        steps=["сварить"],
        macros=Macros(kcal=day_kcal, protein_g=20, fat_g=10, carbs_g=80),
    )
    day = MenuDay(day_index=1, totals=Macros(kcal=0, protein_g=0, fat_g=0, carbs_g=0), meals=[meal])
    return MenuOut(
        days_count=1,
        total_per_day=Macros(kcal=0, protein_g=0, fat_g=0, carbs_g=0),
        days=[day],
    )


def test_no_target_no_adjustment():
    from app.services.nutrition import correct_macros

    menu = _menu(1500)
    assert correct_macros(menu, None) is False
    assert menu.days[0].totals.kcal == 1500
    assert menu.total_per_day.kcal == 1500


def test_within_tolerance_not_scaled():
    from app.services.nutrition import correct_macros

    profile = Profile(target_kcal=2000)
    menu = _menu(1900)  # 5% off, within ±10%
    assert correct_macros(menu, profile) is False
    assert menu.days[0].totals.kcal == 1900


def test_scaled_to_target():
    from app.services.nutrition import correct_macros

    profile = Profile(target_kcal=2000)
    menu = _menu(1000)  # 50% off → rescaled
    assert correct_macros(menu, profile) is True
    assert menu.days[0].totals.kcal == 2000
    # Ingredient amount scaled by factor 2.0
    assert menu.days[0].meals[0].ingredients[0].amount == 200
