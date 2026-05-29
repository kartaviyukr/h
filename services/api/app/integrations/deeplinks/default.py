from app.integrations.deeplinks.base import CartLink, DeepLinkItem


class DefaultDeepLinkBuilder:
    """Fallback builder: per-item URLs from the offer; no aggregated cart URL.

    Provider-specific builders override `aggregated_url` when supported.
    """

    code = "default"

    def build(self, provider_code: str, items: list[dict]) -> CartLink:
        per_item = [DeepLinkItem(name=item["name"], url=item.get("url")) for item in items]
        return CartLink(aggregated_url=None, items=per_item)
