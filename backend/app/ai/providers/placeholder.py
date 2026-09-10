"""Development-only inference provider.

This provider exists so the full analysis lifecycle, API, and tests can run
without a real model. It returns a *deterministic, clearly-labelled development
result*. It is NOT a trained model and must never be presented as real AI:

- provider/model metadata carry `development-placeholder`
- `is_placeholder` is persisted with every result
- confidence values are conservative and deterministic (never fabricated
  accuracy metrics)
- language stays tentative ("may be consistent with"), never certainty
"""

from __future__ import annotations

from app.ai.types import AnalysisInput, InferenceResult
from app.domain.enums import (
    ActivityState,
    AudioCategory,
    BehaviorState,
    ObservationCategory,
    OwnerPresence,
)
from app.domain.value_objects import ModelIdentity, Observation

IDENTITY = ModelIdentity(
    provider="development-placeholder",
    model_name="barkly-placeholder",
    model_version="0.0.0-development",
    is_placeholder=True,
)

_SOUND_BEHAVIOR: dict[str, tuple[str, float, Observation]] = {
    AudioCategory.BARK.value: (
        BehaviorState.ATTENTION_SEEKING.value,
        0.78,
        Observation(ObservationCategory.AUDIO, "Repeated vocalization detected."),
    ),
    AudioCategory.WHINE.value: (
        BehaviorState.RESTLESS.value,
        0.72,
        Observation(ObservationCategory.AUDIO, "High-pitched continuous vocalization detected."),
    ),
    AudioCategory.WHIMPER.value: (
        BehaviorState.STRESSED.value,
        0.69,
        Observation(ObservationCategory.AUDIO, "Soft, low-amplitude vocalization detected."),
    ),
    AudioCategory.GROWL.value: (
        BehaviorState.AGGRESSIVE.value,
        0.66,
        Observation(ObservationCategory.AUDIO, "Low-frequency growl detected."),
    ),
    AudioCategory.HOWL.value: (
        BehaviorState.ALERT.value,
        0.70,
        Observation(ObservationCategory.AUDIO, "Sustained howl detected."),
    ),
    AudioCategory.SIGH.value: (
        BehaviorState.RELAXED.value,
        0.68,
        Observation(ObservationCategory.AUDIO, "Single low-energy vocalization detected."),
    ),
}

_INPUT_FALLBACK: dict[str, tuple[str, float, Observation]] = {
    "AUDIO": (
        BehaviorState.CURIOUS.value,
        0.65,
        Observation(
            ObservationCategory.AUDIO,
            "Vocal activity detected with ambiguous characteristics.",
        ),
    ),
    "VIDEO": (
        BehaviorState.PLAYFUL.value,
        0.71,
        Observation(ObservationCategory.VISUAL, "Movement pattern detected; frames available."),
    ),
    "IMAGE": (
        BehaviorState.RELAXED.value,
        0.68,
        Observation(ObservationCategory.VISUAL, "Static body posture captured."),
    ),
    "BEHAVIOR": (
        BehaviorState.CURIOUS.value,
        0.70,
        Observation(ObservationCategory.CONTEXT, "Behavioral notes provided by the owner."),
    ),
}


class DevelopmentPlaceholderProvider:
    identity = IDENTITY

    async def analyze(self, request: AnalysisInput) -> InferenceResult:
        observations: list[Observation] = []
        primary = BehaviorState.UNKNOWN.value
        confidence = 0.55
        detected_audio: AudioCategory | None = None

        if request.audio is not None and request.audio.sound_category is not None:
            category = request.audio.sound_category
            detected_audio = category
            primary, confidence, observation = _SOUND_BEHAVIOR[category.value]
            observations.append(observation)
        else:
            primary, confidence, observation = _INPUT_FALLBACK[request.input_type.value]
            observations.append(observation)

        if request.input_type.value == "VIDEO":
            observations.append(
                Observation(
                    ObservationCategory.VISUAL,
                    "Timestamped frames available for review.",
                )
            )

        context_bumps: list[str] = []
        context = request.context
        if context.owner_presence == OwnerPresence.AWAY:
            context_bumps.append("Owner away from home.")
        elif context.owner_presence == OwnerPresence.HOME:
            context_bumps.append("Owner present at home.")
        if context.activity_state == ActivityState.PLAYING:
            context_bumps.append("Play activity reported.")
        if context.recent_stressful_event:
            context_bumps.append("Stressful event reported near the capture time.")
        if context.recent_walk is False:
            context_bumps.append("No recent walk reported.")

        for bump in context_bumps:
            observations.append(Observation(ObservationCategory.CONTEXT, bump))

        explanation = (
            "The observed pattern appears consistent with "
            f"{BehaviorState(primary).value.lower().replace('_', ' ')} behavior "
            "based on the available signals and context. This is an estimate, "
            "not a confirmed interpretation."
        )

        return InferenceResult(
            primary_behavior=primary,
            confidence=round(confidence, 2),
            secondary_behaviors=[BehaviorState.UNKNOWN.value],
            observations=observations,
            explanation=explanation,
            detected_audio_category=detected_audio,
            model=IDENTITY,
        )

    async def health(self) -> bool:
        return True
