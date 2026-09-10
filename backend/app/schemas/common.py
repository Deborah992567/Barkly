"""Shared schema base and reusable field constraints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    """Project-wide base schema: explicit, configurable, serialization-safe."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=False)


class ConfidenceMixin(APIModel):
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Estimated confidence in the primary behavior."
    )


class Timestamped(APIModel):
    created_at: datetime
    updated_at: datetime
