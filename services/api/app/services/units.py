import math
from decimal import Decimal

# Unit conversion to a per-group base unit:
#   - mass   → grams
#   - volume → millilitres
#   - piece  → pieces

_MASS = {
    "г": 1, "гр": 1, "грамм": 1, "граммов": 1, "грамма": 1, "g": 1,
    "кг": 1000, "kg": 1000, "килограмм": 1000,
}
_VOLUME = {
    "мл": 1, "ml": 1, "миллилитр": 1,
    "л": 1000, "l": 1000, "литр": 1000, "литра": 1000,
}
_PIECE = {"шт": 1, "штук": 1, "штука": 1, "штуки": 1, "pcs": 1, "уп": 1, "упаковка": 1}

_GROUPS = {"g": _MASS, "ml": _VOLUME, "pcs": _PIECE}


def to_base(amount: float, unit: str) -> tuple[float, str] | None:
    """Convert (amount, unit) to (base_amount, base_unit_group). None if unknown unit."""
    u = unit.strip().lower().rstrip(".")
    for group, table in _GROUPS.items():
        if u in table:
            return amount * table[u], group
    return None


def package_cost(
    required_base: float,
    group: str,
    offer_base_unit: str,
    package_size: float,
    package_price: Decimal,
    proportional: bool = False,
) -> tuple[Decimal, float | None] | None:
    """Cost for the required amount given an offer's package; None if units mismatch.

    Returns (cost, packages_to_buy). In proportional mode packages_to_buy is None.
    """
    if offer_base_unit != group or package_size <= 0:
        return None
    if proportional:
        cost = package_price * Decimal(str(required_base / package_size))
        return cost.quantize(Decimal("0.01")), None
    packages = math.ceil(required_base / package_size)
    cost = (package_price * packages).quantize(Decimal("0.01"))
    return cost, float(packages)
