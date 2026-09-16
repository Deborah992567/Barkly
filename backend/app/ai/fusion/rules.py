"""Evidence-based interpretation rules for BARKLY Phase 4.

These are the ONLY mappings between observable evidence and candidate
interpretations. Rules require at least one known (non-UNKNOWN) model output
before a behavioral hypothesis is produced. They intentionally do NOT make
simple one-signal claims such as "bark → aggression": the Phase 3 models do not
support emotion classification, and no rule emits AGGRESSIVE, FEARFUL, or
DISTRESSED as a *primary* claim.

Supported evidence (from the actual Phase 3 models):
- audio activity classes (barkopedia-activity-env): alerting_to_sounds,
  begging_for_food, playing_with_human, playing_with_other_animals,
  playing_with_toy, rest, seeking_attention, taking_shower
- vision pose classes (dogpose-cv): standing, sitting, lying, undefined

Rules are ordered; the first rule whose REQUIRED hints are satisfied wins.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import BehaviorState, BehavioralHints


@dataclass(frozen=True)
class InterpretationRule:
    id: str
    interpretation: BehaviorState
    required_hints: tuple[BehavioralHints, ...]
    supporting_hints: tuple[BehavioralHints, ...]
    contradicting_hints: tuple[BehavioralHints, ...]
    alternatives: tuple[BehaviorState, ...]


RULES: tuple[InterpretationRule, ...] = (
    InterpretationRule(
        id="play-from-activity",
        interpretation=BehaviorState.PLAYFUL,
        required_hints=(BehavioralHints.AUDIO_PLAYING,),
        supporting_hints=(
            BehavioralHints.CONTEXT_PLAYING,
            BehavioralHints.RECENT_PLAY,
            BehavioralHints.OTHER_ANIMALS_PRESENT,
        ),
        contradicting_hints=(BehavioralHints.AUDIO_REST, BehavioralHints.VISION_LYING),
        alternatives=(BehaviorState.EXCITED,),
    ),
    InterpretationRule(
        id="attention-from-activity",
        interpretation=BehaviorState.ATTENTION_SEEKING,
        required_hints=(BehavioralHints.AUDIO_ATTENTION, BehavioralHints.AUDIO_FOOD),
        supporting_hints=(
            BehavioralHints.OWNER_PRESENT,
            BehavioralHints.RECENT_FEEDING,
        ),
        contradicting_hints=(BehavioralHints.AUDIO_REST,),
        alternatives=(BehaviorState.EXCITED,),
    ),
    InterpretationRule(
        id="alert-from-activity",
        interpretation=BehaviorState.ALERT,
        required_hints=(BehavioralHints.AUDIO_ALERTING,),
        supporting_hints=(
            BehavioralHints.STRANGERS_PRESENT,
            BehavioralHints.OTHER_ANIMALS_PRESENT,
            BehavioralHints.RECENT_STRESS,
            BehavioralHints.OWNER_AWAY,
            BehavioralHints.VISION_STANDING,
        ),
        contradicting_hints=(BehavioralHints.AUDIO_REST, BehavioralHints.VISION_LYING),
        alternatives=(BehaviorState.ATTENTION_SEEKING,),
    ),
    InterpretationRule(
        id="relaxed-from-rest-or-pose",
        interpretation=BehaviorState.RELAXED,
        required_hints=(BehavioralHints.AUDIO_REST, BehavioralHints.VISION_LYING),
        supporting_hints=(BehavioralHints.CONTEXT_RESTING,),
        contradicting_hints=(
            BehavioralHints.AUDIO_ALERTING,
            BehavioralHints.AUDIO_PLAYING,
            BehavioralHints.AUDIO_ATTENTION,
            BehavioralHints.VISION_STANDING,
        ),
        alternatives=(),
    ),
)


def rule_for_interpretation(state: BehaviorState) -> InterpretationRule | None:
    for rule in RULES:
        if rule.interpretation is state:
            return rule
    return None