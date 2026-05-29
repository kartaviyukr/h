from app.integrations.deeplinks.base import DeepLinkBuilder
from app.integrations.deeplinks.default import DefaultDeepLinkBuilder

# provider code → specific builder. Real adapters (Самокат/СберМаркет/...) land here.
_BUILDERS: dict[str, DeepLinkBuilder] = {}
_DEFAULT = DefaultDeepLinkBuilder()


def get_builder(provider_code: str) -> DeepLinkBuilder:
    return _BUILDERS.get(provider_code, _DEFAULT)
