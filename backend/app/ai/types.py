"""HTTP-independent internal representation for AI inference.

These types sit between services and providers. They are decoupled from HTTP
schemas and from any specific ML framework so future models can map their
output into this contract without touching the API layer.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.domain.enums import (
    ActivityState,
    AnalysisInputType,
    AudioCategory,
    OwnerPresence,
    TimeOfDayCategory,
)
from app.domain.value_objects import ModelIdentity, Observation


@dataclass(frozen=True)
class DogContext:
    dog_id: uuid.UUID
    age_years: int | None
    breed: str | None
    sex: str | None


@dataclass(frozen=True)
class AudioSignal:
    duration_ms: int | None
    sound_category: AudioCategory | None


@dataclass(frozen=True)
class VisualSignal:
    media_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class MediaRef:
    """A stored media asset a provider can resolve through the storage layer."""

    media_type: str
    storage_reference: str
    duration_ms: int | None = None


@dataclass(frozen=True)
class ContextSignals:
    owner_presence: OwnerPresence | None = None
    activity_state: ActivityState | None = None
    time_of_day: TimeOfDayCategory | None = None
    recent_feeding: bool | None = None
    recent_walk: bool | None = None
    recent_play: bool | None = None
    presence_of_strangers: bool | None = None
    presence_of_other_animals: bool | None = None
    recent_stressful_event: bool | None = None
    location_category: str | None = None

    def present(self) -> list[str]:
        names: list[str] = []
        for field_name, value in self.__dict__.items():
            if value is not None:
                names.append(field_name)
        return names


@dataclass(frozen=True)
class AnalysisInput:
    dog: DogContext
    input_type: AnalysisInputType
    audio: AudioSignal | None = None
    visual: VisualSignal = field(default_factory=VisualSignal)
    context: ContextSignals = field(default_factory=ContextSignals)
    media_refs: tuple[MediaRef, ...] = ()


@dataclass(frozen=True)
class SignalAvailability:
    """Which modality signals were available and usable for this analysis."""

    audio_available: bool = False
    video_available: bool = False
    context_available: bool = False
    audio_quality: str | None = None  # "good" | "low" | "none"
    video_quality: str | None = None  # "good" | "low" | "none"
    context_completeness: str | None = None  # "high" | "partial" | "none"


@dataclass(frozen=True)
class ModelTrace:
    """Version metadata recorded with a result for full traceability."""

    audio_model_name: str | None = None
    audio_model_version: str | None = None
    vision_model_name: str | None = None
    vision_model_version: str | None = None
    preprocessing_version: str | None = None
    dataset_version: str | None = None
    fusion_version: str | None = None
    interpretation_version: str | None = None


@dataclass(frozen=True)
class InferenceResult:
    primary_behavior: str
    confidence: float
    secondary_behaviors: list[str]
    observations: list[Observation]
    explanation: str
    detected_audio_category: AudioCategory | None
    model: ModelIdentity
    signals: SignalAvailability = field(default_factory=SignalAvailability)
    trace: ModelTrace = field(default_factory=ModelTrace)
    inference_latency_ms: int | None = None
    is_insufficient_evidence: bool = False
    safety_note: str | None = None
