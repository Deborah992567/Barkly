"""Analysis lifecycle, result, and history schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.enums import (
    AnalysisInputType,
    AnalysisStatus,
    AudioCategory,
    BehaviorState,
    ObservationCategory,
)
from app.schemas.common import APIModel, ConfidenceMixin
from app.schemas.context import AnalysisContextCreate, AnalysisContextRead
from app.schemas.media import MediaAssetRead


class ObservationRead(APIModel):
    category: ObservationCategory
    description: str


class AnalysisCreateRequest(APIModel):
    dog_id: UUID
    input_type: AnalysisInputType
    media_ids: list[UUID] = Field(default_factory=list, max_length=8)
    sound_category: AudioCategory | None = None
    duration_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    context: AnalysisContextCreate | None = None
    idempotency_key: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9_-]+$",
    )

    @model_validator(mode="after")
    def _validate_input_shapes(self) -> AnalysisCreateRequest:
        media_based = self.input_type in (
            AnalysisInputType.AUDIO,
            AnalysisInputType.VIDEO,
            AnalysisInputType.IMAGE,
        )
        if media_based and not self.media_ids:
            raise ValueError(f"{self.input_type.value} analysis requires at least one media_id.")
        if self.input_type == AnalysisInputType.BEHAVIOR and self.media_ids:
            raise ValueError("BEHAVIOR analysis cannot reference media.")
        if self.sound_category is not None and self.input_type != AnalysisInputType.AUDIO:
            raise ValueError("sound_category only applies to AUDIO analysis.")
        if self.duration_ms is not None and self.input_type not in (
            AnalysisInputType.AUDIO,
            AnalysisInputType.VIDEO,
        ):
            raise ValueError("duration_ms only applies to audio or video analysis.")
        return self


class FailureRead(APIModel):
    code: str
    message: str


class AnalysisResultRead(ConfidenceMixin):
    primary_behavior: BehaviorState
    secondary_behaviors: list[BehaviorState]
    detected_audio_category: AudioCategory | None
    observations: list[ObservationRead]
    explanation: str
    disclaimer: str
    provider: str
    model_name: str
    model_version: str
    is_placeholder: bool
    generated_at: datetime


class AnalysisStatusRead(APIModel):
    """Explicit state so clients never infer lifecycle from missing fields."""

    analysis_id: UUID
    dog_id: UUID
    status: AnalysisStatus
    input_type: AnalysisInputType
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    failure: FailureRead | None
    result: AnalysisResultRead | None


class AnalysisRead(AnalysisStatusRead):
    media: list[MediaAssetRead]
    context: AnalysisContextRead | None = None
