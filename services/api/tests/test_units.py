from decimal import Decimal

from app.services.units import package_cost, to_base


def test_to_base_mass_kg_to_g():
    assert to_base(1.5, "кг") == (1500.0, "g")


def test_to_base_volume_l_to_ml():
    assert to_base(2, "л") == (2000.0, "ml")


def test_to_base_pieces():
    assert to_base(3, "шт") == (3.0, "pcs")


def test_to_base_unknown_unit():
    assert to_base(100, "пучок") is None


def test_package_cost_rounds_up_to_whole_packages():
    cost, packages = package_cost(
        required_base=1500,
        group="g",
        offer_base_unit="g",
        package_size=1000,
        package_price=Decimal("350.00"),
    )
    assert packages == 2
    assert cost == Decimal("700.00")


def test_package_cost_proportional_skips_rounding():
    cost, packages = package_cost(
        required_base=1500,
        group="g",
        offer_base_unit="g",
        package_size=1000,
        package_price=Decimal("350.00"),
        proportional=True,
    )
    assert packages is None
    assert cost == Decimal("525.00")


def test_package_cost_unit_group_mismatch():
    assert (
        package_cost(
            required_base=300,
            group="g",
            offer_base_unit="ml",
            package_size=1000,
            package_price=Decimal("100"),
        )
        is None
    )
