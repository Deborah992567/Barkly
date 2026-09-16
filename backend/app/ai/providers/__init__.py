"""Provider registry.

The configured provider name is resolved here so services never import a
concrete provider class directly.
"""

from __future__ import annotations

from functools import lru_cache

from app.ai.base import BehaviorInferenceProvider
from app.ai.providers.barkly_models import BarklyModelsProvider
from app.ai.providers.placeholder import DevelopmentPlaceholderProvider


class ProviderConfigurationError(RuntimeError):
    pass


@lru_cache
def get_provider(name: str) -> BehaviorInferenceProvider:
    if name == "development-placeholder":
        return DevelopmentPlaceholderProvider()
    if name == "barkly-models":
        return BarklyModelsProvider()
    raise ProviderConfigurationError(f"Unknown AI provider: {name}")
