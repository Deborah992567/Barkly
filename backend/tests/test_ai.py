"""AI abstraction: provider interface, registry, and placeholder behavior."""

from __future__ import annotations

import uuid

from app.ai.providers import ProviderConfigurationError, get_provider
from app.ai.providers.placeholder import DevelopmentPlaceholderProvider
from app.ai.types import AnalysisInput, AudioSignal, ContextSignals, DogContext
from app.domain.enums import (
    ActivityState,
    AnalysisInputType,
    AudioCategory,
    BehaviorState,
    OwnerPresence,
)
from app.domain.value_objects import ModelIdentity, ObservationCategory


def _input(audio: bool = False, context: ContextSignals | None = None) -> AnalysisInput:
    return AnalysisInput(
        dog=DogContext(
            dog_id=uuid.uuid4(),
            age_years=3,
            breed="Beagle",
            sex="MALE",
        ),
        input_type=AnalysisInputType.AUDIO if audio else AnalysisInputType.VIDEO,
        audio=(AudioSignal(duration_ms=2000, sound_category=AudioCategory.BARK) if audio else None),
        context=context or ContextSignals(),
    )


async def test_placeholder_implements_provider_interface() -> None:
    provider: DevelopmentPlaceholderProvider = get_provider("development-placeholder")
    assert isinstance(provider.identity, ModelIdentity)
    assert provider.identity.is_placeholder is True
    assert provider.identity.provider == "development-placeholder"
    assert await provider.health() is True
    result = await provider.analyze(_input(audio=True))
    assert result.model == provider.identity


async def test_placeholder_is_clearly_marked_non_ai() -> None:
    provider = get_provider("development-placeholder")
    result = await provider.analyze(_input(audio=True))
    assert result.model.model_name == "barkly-placeholder"
    assert result.model.model_version == "0.0.0-development"
    assert result.model.is_placeholder is True


async def test_placeholder_deterministic_mapping() -> None:
    provider = get_provider("development-placeholder")
    first = await provider.analyze(_input(audio=True))
    second = await provider.analyze(_input(audio=True))
    assert first == second
    assert first.primary_behavior == BehaviorState.ATTENTION_SEEKING.value
    assert first.detected_audio_category == AudioCategory.BARK
    assert 0.0 <= first.confidence <= 1.0
    assert any(obs.category == ObservationCategory.AUDIO for obs in first.observations)


async def test_placeholder_uses_context_signals() -> None:
    provider = get_provider("development-placeholder")
    result = await provider.analyze(
        _input(
            audio=True,
            context=ContextSignals(
                owner_presence=OwnerPresence.AWAY,
                activity_state=ActivityState.PLAYING,
                recent_stressful_event=True,
            ),
        )
    )
    context_observations = [
        obs for obs in result.observations if obs.category == ObservationCategory.CONTEXT
    ]
    assert any("Owner away" in obs.description for obs in context_observations)
    assert any("Play activity" in obs.description for obs in context_observations)
    assert any("Stressful event" in obs.description for obs in context_observations)


async def test_unknown_provider_rejected() -> None:
    try:
        get_provider("does-not-exist")
    except ProviderConfigurationError:
        pass
    else:
        raise AssertionError("unknown provider should raise")
