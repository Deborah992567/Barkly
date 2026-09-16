"""Structured evidence collected from model inference and context.

Evidence is deliberately separate from interpretation: observations describe
what was detected; the fusion/interpretation layer decides what a combination
of observations might mean — and may decide there is not enough evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.ai.types import ContextSignals
from app.domain.enums import BehavioralHints, OwnerPresence


@dataclass(frozen=True)
class AudioEvidence:
    """Output of the Phase 3 audio (activity) model after the policy layer."""

    available: bool = False
    label: str | None = None
    confidence: float = 0.0
    raw_confidence: float = 0.0
    is_unknown: bool = True
    is_ood: bool = False
    is_weak_model: bool = True
    model_version: str | None = None
    supporting_signals: dict[str, float] = field(default_factory=dict)

    def to_observation(self) -> str | None:
        if not self.available or self.is_unknown or self.label is None:
            return None
        return _AUDIO_OBSERVATION_TEMPLATES.get(
            self.label,
            f"Audio patterns consistent with '{self.label.replace('_', ' ')}' were detected.",
        )


@dataclass(frozen=True)
class PoseSignal:
    pose: str
    confidence: float


@dataclass(frozen=True)
class VisualEvidence:
    """Aggregated output of the Phase 3 vision (pose) model."""

    available: bool = False
    aggregated_pose: str | None = None
    confidence: float = 0.0
    is_unknown: bool = True
    model_version: str | None = None
    frames_sampled: int = 0
    poses: list[PoseSignal] = field(default_factory=list)

    def to_observation(self) -> str | None:
        if not self.available or self.is_unknown or self.aggregated_pose is None:
            return None
        return _POSE_OBSERVATION_TEMPLATES.get(
            self.aggregated_pose,
            f"A '{self.aggregated_pose.replace('_', ' ')}' posture was detected.",
        )


@dataclass(frozen=True)
class ContextEvidence:
    """Context is supporting evidence only; it can never override model signals."""

    available: bool = False
    signals: ContextSignals = field(default_factory=ContextSignals)

    def present(self) -> list[str]:
        return self.signals.present()

    def hints(self) -> set[BehavioralHints]:
        hints: set[BehavioralHints] = set()
        s = self.signals
        if s.owner_presence == OwnerPresence.HOME:
            hints.add(BehavioralHints.OWNER_PRESENT)
        elif s.owner_presence == OwnerPresence.AWAY:
            hints.add(BehavioralHints.OWNER_AWAY)
        if s.recent_play is True:
            hints.add(BehavioralHints.RECENT_PLAY)
        if s.recent_walk is True:
            hints.add(BehavioralHints.RECENT_WALK)
        if s.recent_feeding is True:
            hints.add(BehavioralHints.RECENT_FEEDING)
        if s.recent_stressful_event is True:
            hints.add(BehavioralHints.RECENT_STRESS)
        if s.presence_of_strangers is True:
            hints.add(BehavioralHints.STRANGERS_PRESENT)
        if s.presence_of_other_animals is True:
            hints.add(BehavioralHints.OTHER_ANIMALS_PRESENT)
        if s.activity_state is not None:
            if str(s.activity_state) == "PLAYING":
                hints.add(BehavioralHints.CONTEXT_PLAYING)
            elif str(s.activity_state) == "RESTING":
                hints.add(BehavioralHints.CONTEXT_RESTING)
        if s.time_of_day is not None and str(s.time_of_day) == "NIGHT":
            hints.add(BehavioralHints.NIGHTTIME)
        return hints


@dataclass(frozen=True)
class EvidenceBundle:
    audio: AudioEvidence = field(default_factory=AudioEvidence)
    visual: VisualEvidence = field(default_factory=VisualEvidence)
    context: ContextEvidence = field(default_factory=ContextEvidence)


_AUDIO_OBSERVATION_TEMPLATES: dict[str, str] = {
    "alerting_to_sounds": "Audio patterns consistent with a dog alerting to sounds were detected.",
    "begging_for_food": "Audio patterns consistent with begging for food were detected.",
    "playing_with_human": "Audio patterns consistent with playing with a person were detected.",
    "playing_with_other_animals": (
        "Audio patterns consistent with playing with other animals were detected."
    ),
    "playing_with_toy": "Audio patterns consistent with playing with a toy were detected.",
    "rest": "Audio patterns consistent with rest were detected.",
    "seeking_attention": "Audio patterns consistent with attention-seeking were detected.",
    "taking_shower": "Audio patterns consistent with a shower environment were detected.",
}

_POSE_OBSERVATION_TEMPLATES: dict[str, str] = {
    "standing": "An upright standing posture was detected.",
    "sitting": "A sitting posture was detected.",
    "lying": "A lying-down posture was detected.",
    "undefined": "A defined posture could not be resolved from the frames.",
}
