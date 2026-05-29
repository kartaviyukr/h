from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DeepLinkItem:
    name: str
    url: str | None


@dataclass(frozen=True)
class CartLink:
    aggregated_url: str | None
    items: list[DeepLinkItem]


class DeepLinkBuilder(Protocol):
    code: str

    def build(self, provider_code: str, items: list[dict]) -> CartLink:
        """Return per-item deep links and an optional aggregated cart URL."""
        ...
