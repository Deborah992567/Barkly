"""AI inference provider interface.

The API/service layers depend only on this interface. Future providers
(audio model, vision model, multimodal model, personalized model) can be
plugged in without changing API code.
"""

from __future__ import annotations

from typing import Protocol

from app.ai.types import AnalysisInput, InferenceResult
from app.domain.value_objects import ModelIdentity


class ProviderError(Exception):
    """Base failure from an inference provider."""


class ProviderTimeoutError(ProviderError):
    """Inference exceeded the configured time budget."""


class ProviderUnavailableError(ProviderError):
    """Inference could not be attempted (model serving unavailable)."""


class BehaviorInferenceProvider(Protocol):
    identity: ModelIdentity

    async def analyze(self, request: AnalysisInput) -> InferenceResult:
        """Run inference for one analysis input."""
        ...

    async def health(self) -> bool:
        """Return True when the provider can accept work."""
        ...
