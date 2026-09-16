"""BarklyModelsProvider: real-model integration tests.

These tests exercise the actual Phase 3 artifacts when they are present on disk
(both model files + ffmpeg). They are skipped automatically in CI or on machines
without the gitignored artifacts, keeping the suite hermetic by default.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.ai.providers.barkly_models import BarklyModelsProvider
from app.ai.types import AnalysisInput, AudioSignal, ContextSignals, DogContext
from app.core.config import get_settings
from app.domain.enums import AnalysisInputType, BehaviorState, OwnerPresence

pytestmark = pytest.mark.asyncio


def _artifacts_present() -> bool:
    settings = get_settings()
    root = Path(__file__).resolve().parents[2]
    return (
        (root / settings.ai_audio_model_path.lstrip("/")).is_file()
        and (root / settings.ai_vision_model_path.lstrip("/")).is_file()
    )


@pytest.mark.skipif(not _artifacts_present(), reason="Phase 3 model artifacts not on disk")
async def test_provider_health_reflects_artifacts() -> None:
    provider = BarklyModelsProvider()
    assert await provider.health() is True


@pytest.mark.skipif(not _artifacts_present(), reason="Phase 3 model artifacts not on disk")
async def test_provider_identity_is_not_placeholder() -> None:
    provider = BarklyModelsProvider()
    assert provider.identity.is_placeholder is False
    assert provider.identity.provider == "barkly-models"


@pytest.mark.skipif(not _artifacts_present(), reason="Phase 3 model artifacts not on disk")
async def test_provider_audio_only_unknown_is_honest() -> None:
    provider = BarklyModelsProvider()
    request = AnalysisInput(
        dog=DogContext(
            dog_id=uuid.uuid4(),
            age_years=4,
            breed="Mixed",
            sex="MALE",
        ),
        input_type=AnalysisInputType.AUDIO,
        audio=AudioSignal(duration_ms=None, sound_category=None),
        context=ContextSignals(owner_presence=OwnerPresence.AWAY),
    )
    result = await provider.analyze(request)
    # No media refs → no model signal → must be an honest UNKNOWN, never a
    # fabricated play/alert interpretation.
    assert result.primary_behavior == BehaviorState.UNKNOWN
    assert result.is_insufficient_evidence is True
    assert result.model.provider == "barkly-models"
    assert result.trace.audio_model_name is not None
    assert result.trace.fusion_version == get_settings().ai_fusion_version
