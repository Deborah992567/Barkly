"""Deterministic fusion + interpretation unit tests (synthetic evidence).

These tests pin the documented uncertainty policy:
- requires a KNOWN model signal before any interpretation is produced
- taking_shower / unknown audio → UNKNOWN, never a behavior claim
- strong cross-modal contradiction → UNKNOWN primary preserving both signals
- context can only support or (softly) conflict; it never drives a decision
- aggression/fear/distress are never produced by any known-signal path
"""

from __future__ import annotations

from app.ai.evidence import (
    AudioEvidence,
    ContextEvidence,
    EvidenceBundle,
    VisualEvidence,
)
from app.ai.fusion.engine import FusionEngine
from app.ai.fusion.interpretation import interpret
from app.ai.types import ContextSignals, ModelTrace
from app.core.config import get_settings
from app.domain.enums import (
    ActivityState,
    BehaviorState,
    ObservationCategory,
    OwnerPresence,
)
from app.domain.value_objects import ModelIdentity

MODEL = ModelIdentity(
    provider="barkly-models",
    model_name="barkly-multimodal-v1",
    model_version="1.0.0",
)


def _analyze(bundle: EvidenceBundle) -> tuple:
    engine = FusionEngine()
    outcome = engine.fuse(bundle)
    result = interpret(
        outcome=outcome,
        evidence=bundle,
        model=MODEL,
        trace=ModelTrace(),
        latency_ms=1,
    )
    return outcome, result


def _audio(label: str, confidence: float, known: bool = True) -> AudioEvidence:
    return AudioEvidence(
        available=True,
        label=label if known else None,
        confidence=confidence,
        raw_confidence=confidence,
        is_unknown=not known,
    )


def _visual(pose: str, confidence: float, known: bool = True) -> VisualEvidence:
    return VisualEvidence(
        available=True,
        aggregated_pose=pose if known else None,
        confidence=confidence,
        is_unknown=not known,
    )


async def test_play_rule_requires_known_activity_audio() -> None:
    bundle = EvidenceBundle(audio=_audio("playing_with_toy", 0.71))
    outcome, result = _analyze(bundle)
    assert outcome.matched_rule is not None
    assert outcome.matched_rule.id == "play-from-activity"
    assert result.primary_behavior == BehaviorState.PLAYFUL
    assert result.confidence >= 0.70
    assert BehaviorState.EXCITED in result.secondary_behaviors
    assert not result.is_insufficient_evidence


async def test_play_audio_with_lying_posture_is_a_conflict() -> None:
    bundle = EvidenceBundle(
        audio=_audio("playing_with_toy", 0.75),
        visual=_visual("lying", 0.90),
    )
    outcome, result = _analyze(bundle)
    assert outcome.strong_conflict is True
    assert result.primary_behavior == BehaviorState.UNKNOWN
    assert result.confidence <= 0.40
    assert BehaviorState.PLAYFUL in result.secondary_behaviors
    categories = {obs.category for obs in result.observations}
    assert ObservationCategory.AUDIO in categories
    assert ObservationCategory.VISUAL in categories


async def test_context_only_cannot_produce_interpretation() -> None:
    bundle = EvidenceBundle(
        context=ContextEvidence(
            available=True,
            signals=ContextSignals(
                owner_presence=OwnerPresence.AWAY,
                activity_state=ActivityState.PLAYING,
                recent_play=True,
                presence_of_strangers=True,
            ),
        )
    )
    outcome, result = _analyze(bundle)
    assert outcome.is_insufficient_evidence is True
    assert result.primary_behavior == BehaviorState.UNKNOWN
    assert result.is_insufficient_evidence is True


async def test_unknown_audio_yields_insufficient_evidence() -> None:
    bundle = EvidenceBundle(audio=_audio("UNKNOWN", 0.17, known=False))
    outcome, result = _analyze(bundle)
    assert result.primary_behavior == BehaviorState.UNKNOWN
    assert result.is_insufficient_evidence is True
    observation = next(
        (o for o in result.observations if o.category == ObservationCategory.AUDIO),
        None,
    )
    assert observation is not None
    assert "could not be confidently classified" in observation.description


async def test_taking_shower_never_becomes_a_behavior() -> None:
    bundle = EvidenceBundle(audio=_audio("taking_shower", 0.80))
    outcome, result = _analyze(bundle)
    assert outcome.matched_rule is None
    assert result.primary_behavior == BehaviorState.UNKNOWN
    assert result.is_insufficient_evidence is False
    assert all(o.category != ObservationCategory.VISUAL for o in result.observations)


async def test_alert_with_strangers_gets_safety_note() -> None:
    bundle = EvidenceBundle(
        audio=_audio("alerting_to_sounds", 0.66),
        context=ContextEvidence(
            available=True,
            signals=ContextSignals(presence_of_strangers=True),
        ),
    )
    outcome, result = _analyze(bundle)
    assert result.primary_behavior == BehaviorState.ALERT
    assert result.safety_note is not None


async def test_relaxed_from_rest_audio_supported_by_context() -> None:
    bundle = EvidenceBundle(
        audio=_audio("rest", 0.62),
        context=ContextEvidence(
            available=True,
            signals=ContextSignals(activity_state=ActivityState.RESTING),
        ),
    )
    outcome, result = _analyze(bundle)
    assert result.primary_behavior == BehaviorState.RELAXED
    assert len(result.observations) >= 2


async def test_no_rule_emits_aggression_fear_or_distress() -> None:
    # Any provider or rule path (including unknown inputs) must never claim
    # these high-stakes states. Assertiveness states are out of scope.
    forbidden = {
        BehaviorState.AGGRESSIVE,
        BehaviorState.FEARFUL,
        BehaviorState.STRESSED,
    }
    bundles = [
        EvidenceBundle(audio=_audio("playing_with_human", 0.95)),
        EvidenceBundle(audio=_audio("alerting_to_sounds", 0.95)),
        EvidenceBundle(audio=_audio("rest", 0.95)),
        EvidenceBundle(audio=_audio("UNKNOWN", 0.05, known=False)),
        EvidenceBundle(audio=_audio("taking_shower", 0.9)),
        EvidenceBundle(),
        EvidenceBundle(visual=_visual("standing", 0.99)),
    ]
    for bundle in bundles:
        _, result = _analyze(bundle)
        assert result.primary_behavior not in forbidden
        assert all(alt not in forbidden for alt in result.secondary_behaviors)


async def test_settings_expose_fusion_policy_document() -> None:
    settings = get_settings()
    assert settings.ai_fusion_contradiction_penalty == 0.25
    assert settings.ai_audio_confidence_threshold == 0.30
    assert settings.ai_vision_confidence_threshold == 0.50
