"""Translation of fusion outcomes into the public InferenceResult contract.

This is the last AI step before a result is persisted and serialized to the
API. It assembles explanation text, secondary (alternative) behaviors, safety
notes, and full model traceability — without inventing certainty.
"""

from __future__ import annotations

from app.ai.evidence import EvidenceBundle
from app.ai.fusion.engine import FusionOutcome
from app.ai.safety import evaluate_safety
from app.ai.types import InferenceResult, ModelTrace, SignalAvailability
from app.domain.enums import AudioCategory, BehaviorState
from app.domain.value_objects import ModelIdentity


def interpret(
    *,
    outcome: FusionOutcome,
    evidence: EvidenceBundle,
    model: ModelIdentity,
    trace: ModelTrace,
    latency_ms: int,
) -> InferenceResult:
    primary = outcome.candidates[0] if outcome.candidates else None
    primary_state = primary.interpretation if primary else BehaviorState.UNKNOWN
    confidence = primary.confidence if primary else 0.0
    secondary = list(primary.alternatives) if primary else []

    safety = evaluate_safety(
        primary_state=primary_state,
        hints=frozenset(h.name for h in outcome.hints),
        is_insufficient_evidence=outcome.is_insufficient_evidence,
    )

    return InferenceResult(
        primary_behavior=primary_state,
        confidence=confidence,
        secondary_behaviors=secondary,
        observations=outcome.observations,
        explanation=outcome.explanation,
        detected_audio_category=AudioCategory.UNKNOWN,
        model=model,
        signals=_signal_availability(evidence),
        trace=trace,
        inference_latency_ms=latency_ms,
        is_insufficient_evidence=outcome.is_insufficient_evidence,
        safety_note=safety.note,
    )


def _signal_availability(evidence: EvidenceBundle) -> SignalAvailability:
    return SignalAvailability(
        audio_available=evidence.audio.available,
        video_available=evidence.visual.available,
        context_available=evidence.context.available,
        audio_quality=_quality(
            evidence.audio.available, evidence.audio.is_unknown
        ),
        video_quality=_quality(
            evidence.visual.available, evidence.visual.is_unknown
        ),
        context_completeness=(
            "high"
            if evidence.context.available and len(evidence.context.present()) >= 3
            else "partial"
            if evidence.context.available
            else "none"
        ),
    )


def _quality(available: bool, is_unknown: bool) -> str:
    if not available:
        return "none"
    return "low" if is_unknown else "good"