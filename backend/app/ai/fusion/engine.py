"""Multimodal fusion engine.

Decisions here are driven by the documented interpretation rules in
`rules.py` and the confidence formula below. Nothing in this module touches the
database or the HTTP layer. The engine is deliberately explainable: every
candidate records which evidence sources fired, which supports were present,
and which contradictions were detected.

Confidence aggregation (documented in docs/multimodal-fusion.md):

    base            = confidence of the driving (required) model evidence
    contradiction   = a known cross-modal hint listed in the rule's
                      contradicting set (e.g. playing audio + lying posture)
    support_bonus   = min(0.12, 0.04 * number of supporting hints)
    confidence      = clamp(base * (1 - CONTRADICTION_PENALTY * contradictions)
                            + support_bonus,
                            0.0, min(0.95, base + 0.12))

A strong cross-modal contradiction does not silently pick the louder signal:
the outcome reports UNKNOWN as the primary interpretation and preserves both
observations with the rule's candidate listed as an alternative.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.ai.evidence import EvidenceBundle
from app.ai.fusion.rules import RULES, InterpretationRule
from app.core.config import get_settings
from app.domain.enums import BehavioralHints, BehaviorState, ObservationCategory
from app.domain.value_objects import Observation

MAX_SUPPORT_BONUS = 0.12
SUPPORT_BONUS_STEP = 0.04
CONFIDENCE_CEILING_DELTA = 0.12
CONFIDENCE_CAP = 0.95
CONFLICT_CONFIDENCE = 0.40


@dataclass(frozen=True)
class Candidate:
    interpretation: BehaviorState
    confidence: float
    alternatives: tuple[BehaviorState, ...]
    sources: tuple[str, ...] = ()
    supports: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()


@dataclass(frozen=True)
class Hint:
    name: BehavioralHints
    modality: str  # "audio" | "vision" | "context"
    confidence: float  # 0.0 for context hints


@dataclass
class FusionOutcome:
    candidates: list[Candidate] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    is_insufficient_evidence: bool = False
    strong_conflict: bool = False
    explanation: str = ""
    matched_rule: InterpretationRule | None = None
    hints: list[Hint] = field(default_factory=list)


_AUDIO_HINT_BY_LABEL: dict[str, BehavioralHints] = {
    "alerting_to_sounds": BehavioralHints.AUDIO_ALERTING,
    "begging_for_food": BehavioralHints.AUDIO_FOOD,
    "playing_with_human": BehavioralHints.AUDIO_PLAYING,
    "playing_with_other_animals": BehavioralHints.AUDIO_PLAYING,
    "playing_with_toy": BehavioralHints.AUDIO_PLAYING,
    "rest": BehavioralHints.AUDIO_REST,
    "seeking_attention": BehavioralHints.AUDIO_ATTENTION,
    "taking_shower": BehavioralHints.AUDIO_SHOWER,
}

_POSE_HINT_BY_LABEL: dict[str, BehavioralHints] = {
    "standing": BehavioralHints.VISION_STANDING,
    "sitting": BehavioralHints.VISION_SITTING,
    "lying": BehavioralHints.VISION_LYING,
}

_RULE_HINT_LABELS: dict[BehavioralHints, str] = {
    BehavioralHints.AUDIO_ALERTING: "alerting-to-sounds activity",
    BehavioralHints.AUDIO_PLAYING: "play activity",
    BehavioralHints.AUDIO_ATTENTION: "attention-seeking activity",
    BehavioralHints.AUDIO_FOOD: "food-begging activity",
    BehavioralHints.AUDIO_REST: "rest activity",
    BehavioralHints.AUDIO_SHOWER: "shower-environment audio",
    BehavioralHints.VISION_STANDING: "standing posture",
    BehavioralHints.VISION_SITTING: "sitting posture",
    BehavioralHints.VISION_LYING: "lying posture",
}


class FusionEngine:
    def __init__(self) -> None:
        settings = get_settings()
        self._penalty = settings.ai_fusion_contradiction_penalty

    def fuse(self, evidence: EvidenceBundle) -> FusionOutcome:
        hints = self._collect_hints(evidence)
        observations = self._collect_observations(evidence)
        outcome = FusionOutcome(
            observations=observations,
            hints=hints,
            matched_rule=None,
        )

        if not self._has_known_model_signal(hints):
            outcome.is_insufficient_evidence = True
            outcome.candidates = [
                Candidate(
                    interpretation=BehaviorState.UNKNOWN,
                    confidence=0.0,
                    alternatives=(),
                )
            ]
            outcome.explanation = (
                "The available signals were not clear enough for BARKLY to identify "
                "a likely behavior. There was not enough evidence to interpret this "
                "confidently."
            )
            return outcome

        matched = self._match_rule(hints)
        if matched is None:
            outcome.candidates = [
                Candidate(
                    interpretation=BehaviorState.UNKNOWN,
                    confidence=0.0,
                    alternatives=(),
                )
            ]
            outcome.explanation = (
                "The detected signals did not match any supported interpretation "
                "pattern. BARKLY could not confidently interpret these signals."
            )
            return outcome

        outcome.matched_rule = matched
        driving_hint, driving_conf = self._driving_signal(hints, matched)
        conflicts = self._cross_modal_conflicts(hints, matched, driving_hint)
        supports = [
            h.name for h in hints if h.name in matched.supporting_hints
        ]
        sources = tuple(
            _RULE_HINT_LABELS.get(h.name, h.name.value).lower()
            if h.name in _RULE_HINT_LABELS
            else h.name.value.lower()
            for h in hints
            if h.name in matched.required_hints or h.name in matched.supporting_hints
        ) or (_RULE_HINT_LABELS.get(driving_hint, str(driving_hint.value)).lower(),)

        if conflicts:
            outcome.strong_conflict = True
            conflict_names = [_RULE_HINT_LABELS.get(c, c.value).lower() for c in conflicts]
            candidate_conf = round(min(driving_conf, CONFLICT_CONFIDENCE), 2)
            outcome.candidates = [
                Candidate(
                    interpretation=BehaviorState.UNKNOWN,
                    confidence=candidate_conf,
                    alternatives=(matched.interpretation,),
                    sources=sources,
                    supports=tuple(name.value.lower() for name in supports),
                    contradictions=tuple(conflict_names),
                )
            ]
            outcome.explanation = self._conflict_explanation(matched, conflict_names)
            return outcome

        base_conf = driving_conf
        support_bonus = min(MAX_SUPPORT_BONUS, SUPPORT_BONUS_STEP * len(supports))
        confidence = round(
            self._clamp(
                base_conf + support_bonus,
                low=0.0,
                high=min(CONFIDENCE_CAP, base_conf + CONFIDENCE_CEILING_DELTA),
            ),
            2,
        )

        outcome.candidates = [
            Candidate(
                interpretation=matched.interpretation,
                confidence=confidence,
                alternatives=matched.alternatives,
                sources=sources,
                supports=tuple(name.value.lower() for name in supports),
                contradictions=(),
            )
        ]
        outcome.explanation = self._interpretation_explanation(matched, supports)
        return outcome

    # --- internals --------------------------------------------------------

    def _collect_hints(self, evidence: EvidenceBundle) -> list[Hint]:
        hints: list[Hint] = []
        if evidence.audio.available and not evidence.audio.is_unknown and evidence.audio.label:
            hint = _AUDIO_HINT_BY_LABEL.get(evidence.audio.label)
            if hint is not None:
                hints.append(Hint(hint, "audio", evidence.audio.confidence))
        known = evidence.visual.available and not evidence.visual.is_unknown
        if known and evidence.visual.aggregated_pose:
            hint = _POSE_HINT_BY_LABEL.get(evidence.visual.aggregated_pose)
            if hint is not None:
                hints.append(Hint(hint, "vision", evidence.visual.confidence))
        hints.extend(Hint(name, "context", 0.0) for name in evidence.context.hints())
        return hints

    def _collect_observations(self, evidence: EvidenceBundle) -> list[Observation]:
        observations: list[Observation] = []
        audio_obs = evidence.audio.to_observation()
        if audio_obs:
            observations.append(Observation(ObservationCategory.AUDIO, audio_obs))
        elif evidence.audio.available:
            observations.append(
                Observation(
                    ObservationCategory.AUDIO,
                    "Audio signals were detected but could not be confidently classified.",
                )
            )
        visual_obs = evidence.visual.to_observation()
        if visual_obs:
            observations.append(Observation(ObservationCategory.VISUAL, visual_obs))
        elif evidence.visual.available:
            observations.append(
                Observation(
                    ObservationCategory.VISUAL,
                    "Video frames were detected but a defined posture could not be resolved.",
                )
            )
        for name in evidence.context.present():
            observations.append(
                Observation(ObservationCategory.CONTEXT, self._context_label(name))
            )
        if not evidence.audio.available and not evidence.visual.available:
            observations.append(
                Observation(
                    ObservationCategory.ENVIRONMENTAL,
                    "No usable audio or visual signals were available for analysis.",
                )
            )
        return observations

    @staticmethod
    def _context_label(name: str) -> str:
        return {
            "owner_presence": "Owner presence was reported at capture time.",
            "activity_state": "A surrounding activity was reported for the capture.",
            "time_of_day": "The capture time of day was reported.",
            "recent_feeding": "Recent feeding was reported.",
            "recent_walk": "A recent walk was reported.",
            "recent_play": "Recent play was reported.",
            "presence_of_strangers": "The presence of strangers was reported.",
            "presence_of_other_animals": "The presence of other animals was reported.",
            "recent_stressful_event": "A stressful event was reported near capture time.",
            "location_category": "A location category was reported for the capture.",
        }.get(name, f"Context signal '{name}' was reported.")

    @staticmethod
    def _has_known_model_signal(hints: list[Hint]) -> bool:
        return any(h.modality in ("audio", "vision") and h.confidence > 0.0 for h in hints)

    @staticmethod
    def _match_rule(hints: list[Hint]) -> InterpretationRule | None:
        hint_names = {h.name for h in hints}
        for rule in RULES:
            if set(rule.required_hints) & hint_names:
                return rule
        return None

    def _driving_signal(
        self, hints: list[Hint], rule: InterpretationRule
    ) -> tuple[BehavioralHints, float]:
        candidates = [
            (h.name, h.confidence)
            for h in hints
            if h.modality in ("audio", "vision")
            and h.name in rule.required_hints
            and h.confidence > 0.0
        ]
        if not candidates:
            model_hints = [
                (h.name, h.confidence)
                for h in hints
                if h.modality in ("audio", "vision") and h.confidence > 0.0
            ]
            candidates = [max(model_hints, key=lambda item: item[1])]
        return max(candidates, key=lambda item: item[1])

    def _cross_modal_conflicts(
        self,
        hints: list[Hint],
        rule: InterpretationRule,
        driving_hint: BehavioralHints,
    ) -> list[BehavioralHints]:
        driving_modality = next(
            (h.modality for h in hints if h.name == driving_hint and h.confidence > 0.0),
            "audio",
        )
        conflicting = [
            h.name
            for h in hints
            if h.confidence > 0.0
            and h.modality != driving_modality
            and h.name in rule.contradicting_hints
        ]
        return conflicting

    @staticmethod
    def _clamp(value: float, *, low: float, high: float) -> float:
        return max(low, min(high, value))

    @staticmethod
    def _interpretation_explanation(
        rule: InterpretationRule, supports: list[BehavioralHints]
    ) -> str:
        text = {
            BehaviorState.PLAYFUL: (
                "The recorded activity and any accompanying context appear consistent "
                "with play. Other interpretations remain possible."
            ),
            BehaviorState.ATTENTION_SEEKING: (
                "The recorded signals appear consistent with attention-seeking activity. "
                "This is an estimate, not a confirmed intention."
            ),
            BehaviorState.ALERT: (
                "The recorded activity may be consistent with a dog alerting to sounds in "
                "its surroundings. This is a cautious estimate."
            ),
            BehaviorState.RELAXED: (
                "The recorded signals appear consistent with a restful, low-energy state. "
                "This is an estimate, not a confirmed interpretation."
            ),
        }.get(rule.interpretation, "The observed signals appear consistent with this estimate.")
        if supports:
            support_names = [
                _RULE_HINT_LABELS.get(s, s.value.replace("_", " ")).lower() for s in supports
            ]
            text += " Supporting context: " + ", ".join(support_names) + "."
        return text

    @staticmethod
    def _conflict_explanation(
        rule: InterpretationRule, conflict_names: list[str]
    ) -> str:
        primary = {
            BehaviorState.PLAYFUL: "play-related activity",
            BehaviorState.ATTENTION_SEEKING: "attention-seeking activity",
            BehaviorState.ALERT: "alerting activity",
            BehaviorState.RELAXED: "rest activity",
        }.get(rule.interpretation, "the detected activity")
        return (
            f"Signals pointed in different directions: {primary} was detected, but "
            + "the visual evidence also showed "
            + ", ".join(conflict_names)
            + ". BARKLY could not confidently choose one interpretation, so it is "
            "reporting both instead. More context may help next time."
        )
