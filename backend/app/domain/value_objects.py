"""Small domain value objects shared across layers.

Kept independent of the HTTP layer: HTTP schemas map *into* these, and AI
providers map *out of* InferenceResult (ai/types.py) which composes them.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import ObservationCategory


@dataclass(frozen=True)
class Observation:
    """An observable signal, kept distinct from any interpretation of it."""

    category: ObservationCategory
    description: str


@dataclass(frozen=True)
class ModelIdentity:
    """Identifies which provider/model produced a result (auditability)."""

    provider: str
    model_name: str
    model_version: str
    is_placeholder: bool = False
