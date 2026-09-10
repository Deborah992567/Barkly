"""Domain vocabulary and schema-boundary validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.enums import (
    AnalysisInputType,
    AnalysisStatus,
    AudioCategory,
    BehaviorState,
    MediaType,
    ObservationCategory,
)
from app.schemas.analyses import AnalysisCreateRequest, AnalysisResultRead
from app.schemas.feedback import FeedbackCreate


def test_behavior_state_taxonomy_is_stable() -> None:
    expected = {
        "RELAXED",
        "ALERT",
        "PLAYFUL",
        "EXCITED",
        "CURIOUS",
        "ATTENTION_SEEKING",
        "FEARFUL",
        "STRESSED",
        "AGGRESSIVE",
        "SUBMISSIVE",
        "RESTLESS",
        "UNKNOWN",
    }
    assert {state.value for state in BehaviorState} == expected


def test_audio_category_taxonomy_is_stable() -> None:
    expected = {"BARK", "WHINE", "WHIMPER", "GROWL", "HOWL", "SIGH", "UNKNOWN"}
    assert {category.value for category in AudioCategory} == expected


def test_analysis_status_values() -> None:
    expected = {"CREATED", "QUEUED", "PROCESSING", "COMPLETED", "FAILED", "CANCELLED"}
    assert {status.value for status in AnalysisStatus} == expected


def test_media_types() -> None:
    assert {m.value for m in MediaType} == {"AUDIO", "VIDEO", "IMAGE"}
    assert {c.value for c in ObservationCategory} >= {"AUDIO", "VISUAL", "CONTEXT"}


def test_confidence_must_be_bounded() -> None:
    AnalysisResultRead(
        primary_behavior=BehaviorState.RELAXED,
        confidence=0.0,
        secondary_behaviors=[],
        detected_audio_category=None,
        observations=[],
        explanation="x",
        disclaimer="x",
        provider="p",
        model_name="m",
        model_version="1",
        is_placeholder=True,
        generated_at="2026-01-01T00:00:00Z",
    )
    with pytest.raises(ValidationError):
        AnalysisResultRead(
            primary_behavior=BehaviorState.RELAXED,
            confidence=1.5,
            secondary_behaviors=[],
            detected_audio_category=None,
            observations=[],
            explanation="x",
            disclaimer="x",
            provider="p",
            model_name="m",
            model_version="1",
            is_placeholder=True,
            generated_at="2026-01-01T00:00:00Z",
        )


def test_audio_analysis_requires_media() -> None:
    with pytest.raises(ValidationError):
        AnalysisCreateRequest(
            dog_id="00000000-0000-0000-0000-000000000001",
            input_type=AnalysisInputType.AUDIO,
            media_ids=[],
        )


def test_sound_category_only_for_audio() -> None:
    with pytest.raises(ValidationError):
        AnalysisCreateRequest(
            dog_id="00000000-0000-0000-0000-000000000001",
            input_type=AnalysisInputType.VIDEO,
            media_ids=["00000000-0000-0000-0000-000000000002"],
            sound_category=AudioCategory.BARK,
        )


def test_behavior_input_cannot_reference_media() -> None:
    with pytest.raises(ValidationError):
        AnalysisCreateRequest(
            dog_id="00000000-0000-0000-0000-000000000001",
            input_type=AnalysisInputType.BEHAVIOR,
            media_ids=["00000000-0000-0000-0000-000000000002"],
        )


def test_duration_only_for_audio_or_video() -> None:
    with pytest.raises(ValidationError):
        AnalysisCreateRequest(
            dog_id="00000000-0000-0000-0000-000000000001",
            input_type=AnalysisInputType.IMAGE,
            media_ids=["00000000-0000-0000-0000-000000000002"],
            duration_ms=5000,
        )


def test_feedback_correction_requires_behavior() -> None:
    with pytest.raises(ValidationError):
        FeedbackCreate(verdict="CORRECTED", corrected_behavior=None)


def test_feedback_confirmed_cannot_correct() -> None:
    with pytest.raises(ValidationError):
        FeedbackCreate(
            verdict="CONFIRMED",
            corrected_behavior=BehaviorState.PLAYFUL,
        )
