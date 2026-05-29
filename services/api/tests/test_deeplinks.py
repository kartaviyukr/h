from app.integrations.deeplinks.default import DefaultDeepLinkBuilder
from app.integrations.deeplinks.registry import get_builder


def test_default_builder_passes_through_urls():
    builder = DefaultDeepLinkBuilder()
    link = builder.build(
        "x", [{"name": "Курица", "url": "https://x.example/p/1"}, {"name": "Молоко", "url": None}]
    )
    assert link.aggregated_url is None
    assert [(i.name, i.url) for i in link.items] == [
        ("Курица", "https://x.example/p/1"),
        ("Молоко", None),
    ]


def test_registry_falls_back_to_default_for_unknown_provider():
    assert isinstance(get_builder("unknown_provider_code"), DefaultDeepLinkBuilder)
