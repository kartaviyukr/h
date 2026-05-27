from app.models.profile import Profile
from app.schemas.menu import Macros, MenuDay, MenuOut

# Allowed deviation from the daily calorie target before we rescale portions.
KCAL_TOLERANCE = 0.10


def _sum_macros(items: list[Macros]) -> Macros:
    return Macros(
        kcal=round(sum(m.kcal for m in items), 1),
        protein_g=round(sum(m.protein_g for m in items), 1),
        fat_g=round(sum(m.fat_g for m in items), 1),
        carbs_g=round(sum(m.carbs_g for m in items), 1),
    )


def _scale_day(day: MenuDay, factor: float) -> None:
    for meal in day.meals:
        meal.macros = Macros(
            kcal=round(meal.macros.kcal * factor, 1),
            protein_g=round(meal.macros.protein_g * factor, 1),
            fat_g=round(meal.macros.fat_g * factor, 1),
            carbs_g=round(meal.macros.carbs_g * factor, 1),
        )
        for ing in meal.ingredients:
            ing.amount = round(ing.amount * factor, 1)


def correct_macros(menu: MenuOut, profile: Profile | None) -> bool:
    """Recompute daily totals; rescale portions toward the calorie target.

    Returns True if any day was rescaled. Mutates `menu` in place.
    """
    target = profile.target_kcal if profile else None
    adjusted = False

    for day in menu.days:
        day_total = _sum_macros([meal.macros for meal in day.meals])
        if target and day_total.kcal > 0:
            deviation = abs(day_total.kcal - target) / target
            if deviation > KCAL_TOLERANCE:
                _scale_day(day, target / day_total.kcal)
                adjusted = True
        day.totals = _sum_macros([meal.macros for meal in day.meals])

    if menu.days:
        n = len(menu.days)
        menu.total_per_day = Macros(
            kcal=round(sum(d.totals.kcal for d in menu.days) / n, 1),
            protein_g=round(sum(d.totals.protein_g for d in menu.days) / n, 1),
            fat_g=round(sum(d.totals.fat_g for d in menu.days) / n, 1),
            carbs_g=round(sum(d.totals.carbs_g for d in menu.days) / n, 1),
        )
    return adjusted
