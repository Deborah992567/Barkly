"""Analysis service: orchestration of the analysis lifecycle.

Flow: validate dog + media + ownership → create record → queue → process →
infer (provider) → persist result → complete. Provider failures transition the
record to FAILED with an explicit failure code so clients see an explicit
retry state instead of guessing.

The inference step never runs inside an open database transaction: creation is
committed before inference, and results are persisted in a separate
transaction, mirroring how a background worker would behave later.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import (
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.ai.providers import get_provider
from app.ai.types import (
    AnalysisInput,
    AudioSignal,
    ContextSignals,
    DogContext,
    MediaRef,
    VisualSignal,
)
from app.core.config import get_settings
from app.core.errors import (
    ErrorCode,
    not_found_error,
)
from app.core.logging import get_logger
from app.db.models import Analysis, AnalysisContext, AnalysisMedia, AnalysisObservation, Dog
from app.domain.enums import AnalysisInputType
from app.repositories.analyses import AnalysisRepository
from app.repositories.dogs import DogRepository
from app.repositories.media import MediaRepository
from app.schemas.analyses import AnalysisCreateRequest
from app.schemas.context import AnalysisContextCreate

logger = get_logger(__name__)


class AnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._analyses = AnalysisRepository(session)
        self._dogs = DogRepository(session)
        self._media = MediaRepository(session)

    async def create(self, user_id: uuid.UUID, payload: AnalysisCreateRequest) -> Analysis:
        dog = await self._dogs.get_by_id_and_owner(payload.dog_id, user_id)
        if dog is None:
            raise not_found_error(ErrorCode.DOG_NOT_FOUND, "The requested dog could not be found.")

        if payload.idempotency_key:
            existing = await self._analyses.get_by_idempotency(user_id, payload.idempotency_key)
            if existing is not None:
                logger.info(
                    "analysis_idempotent_replay",
                    extra={"idempotency_key": payload.idempotency_key},
                )
                return existing

        assets = await self._resolve_media(user_id, payload)

        analysis = await self._analyses.create(user_id=user_id, dog_id=dog.id, payload=payload)
        for asset in assets:
            snapshot = AnalysisMedia(
                analysis_id=analysis.id,
                asset_id=asset.id,
                owner_id=user_id,
                media_type=asset.media_type,
                original_filename=asset.original_filename,
                mime_type=asset.mime_type,
                file_size=asset.file_size,
                duration_ms=(
                    payload.duration_ms if payload.duration_ms is not None else asset.duration_ms
                ),
                storage_reference=asset.storage_reference,
            )
            self._analyses.add_media_source(analysis, snapshot)
        if payload.context is not None:
            self._analyses.add_context(analysis, self._build_context_row(payload.context))
        await self._analyses.queue(analysis)
        await self._session.commit()

        await self._run_lifecycle(analysis, dog, payload, assets)
        return await self._analyses.get_by_id_and_user(analysis.id, user_id) or analysis

    async def _run_lifecycle(
        self,
        analysis: Analysis,
        dog: Dog,
        payload: AnalysisCreateRequest,
        assets: list,
    ) -> None:
        await self._analyses.start_processing(analysis)
        await self._session.commit()

        request = self._build_input(dog, payload, assets)
        provider = get_provider(get_settings().ai_provider)

        try:
            result = await provider.analyze(request)
        except ProviderTimeoutError:
            await self._mark_failed(
                analysis,
                "PROVIDER_TIMEOUT",
                "Analysis timed out while waiting for the model. Please try again.",
            )
        except ProviderUnavailableError:
            await self._mark_failed(
                analysis,
                "PROVIDER_UNAVAILABLE",
                "Behavior analysis is temporarily unavailable. Please try again shortly.",
            )
        except ProviderError as exc:
            logger.error(
                "analysis_provider_error",
                exc_info=exc,
                extra={"analysis_id": str(analysis.id)},
            )
            await self._mark_failed(
                analysis,
                "PROVIDER_ERROR",
                "Behavior analysis failed while processing. Please try again.",
            )
        except Exception as exc:  # noqa: BLE001 - provider is a hard boundary
            logger.error(
                "analysis_inference_unexpected",
                exc_info=exc,
                extra={"analysis_id": str(analysis.id)},
            )
            await self._mark_failed(
                analysis,
                "PROVIDER_ERROR",
                "Behavior analysis failed while processing. Please try again.",
            )
        else:
            await self._persist_result(analysis, result)

    async def _persist_result(self, analysis: Analysis, result) -> None:
        settings = get_settings()
        observations = [
            AnalysisObservation(category=obs.category.value, description=obs.description)
            for obs in result.observations
        ]
        signals = result.signals
        await self._analyses.complete(
            analysis,
            primary_behavior=result.primary_behavior,
            confidence=result.confidence,
            secondary_behaviors=result.secondary_behaviors,
            detected_audio_category=(
                result.detected_audio_category.value
                if result.detected_audio_category is not None
                else None
            ),
            explanation=result.explanation,
            disclaimer=settings.disclaimer,
            provider=result.model.provider,
            model_name=result.model.model_name,
            model_version=result.model.model_version,
            is_placeholder=result.model.is_placeholder,
            observations=observations,
            audio_model_name=result.trace.audio_model_name,
            audio_model_version=result.trace.audio_model_version,
            vision_model_name=result.trace.vision_model_name,
            vision_model_version=result.trace.vision_model_version,
            preprocessing_version=result.trace.preprocessing_version,
            dataset_version=result.trace.dataset_version,
            fusion_version=result.trace.fusion_version,
            interpretation_version=result.trace.interpretation_version,
            inference_latency_ms=result.inference_latency_ms,
            is_insufficient_evidence=result.is_insufficient_evidence,
            signals_available={
                "audio_available": signals.audio_available,
                "video_available": signals.video_available,
                "context_available": signals.context_available,
                "audio_quality": signals.audio_quality,
                "video_quality": signals.video_quality,
                "context_completeness": signals.context_completeness,
            },
        )
        await self._session.commit()
        logger.info(
            "analysis_completed",
            extra={
                "analysis_id": str(analysis.id),
                "provider": result.model.provider,
                "model_version": result.model.model_version,
            },
        )

    async def _mark_failed(self, analysis: Analysis, failure_code: str, message: str) -> None:
        await self._analyses.fail(analysis, failure_code, message)
        await self._session.commit()

    async def _resolve_media(self, user_id: uuid.UUID, payload: AnalysisCreateRequest) -> list:
        assets: list = []
        for media_id in payload.media_ids:
            asset = await self._media.get_by_id_and_owner(media_id, user_id)
            if asset is None:
                raise not_found_error(
                    ErrorCode.RESOURCE_NOT_FOUND,
                    "A referenced media upload could not be found.",
                )
            assets.append(asset)
        return assets

    def _build_context_row(self, context: AnalysisContextCreate) -> AnalysisContext:
        return AnalysisContext(
            owner_presence=context.owner_presence.value if context.owner_presence else None,
            activity_state=context.activity_state.value if context.activity_state else None,
            time_of_day=context.time_of_day.value if context.time_of_day else None,
            recent_feeding=context.recent_feeding,
            recent_walk=context.recent_walk,
            recent_play=context.recent_play,
            presence_of_strangers=context.presence_of_strangers,
            presence_of_other_animals=context.presence_of_other_animals,
            recent_stressful_event=context.recent_stressful_event,
            location_category=context.location_category,
            notes=context.notes,
        )

    def _build_input(self, dog: Dog, payload: AnalysisCreateRequest, assets: list) -> AnalysisInput:
        audio = (
            AudioSignal(
                duration_ms=payload.duration_ms,
                sound_category=payload.sound_category,
            )
            if payload.input_type == AnalysisInputType.AUDIO
            else None
        )
        visual = VisualSignal(
            media_types=tuple(asset.media_type for asset in assets) if assets else ()
        )
        return AnalysisInput(
            dog=DogContext(
                dog_id=dog.id,
                age_years=_age_years(dog.date_of_birth),
                breed=dog.breed,
                sex=dog.sex,
            ),
            input_type=payload.input_type,
            audio=audio,
            visual=visual,
            context=self._map_context(payload.context),
            media_refs=tuple(
                MediaRef(media_type=asset.media_type, storage_reference=asset.storage_reference)
                for asset in assets
            ),
        )

    def _map_context(self, context: AnalysisContextCreate | None) -> ContextSignals:
        if context is None:
            return ContextSignals()
        return ContextSignals(
            owner_presence=context.owner_presence,
            activity_state=context.activity_state,
            time_of_day=context.time_of_day,
            recent_feeding=context.recent_feeding,
            recent_walk=context.recent_walk,
            recent_play=context.recent_play,
            presence_of_strangers=context.presence_of_strangers,
            presence_of_other_animals=context.presence_of_other_animals,
            recent_stressful_event=context.recent_stressful_event,
            location_category=context.location_category,
        )


def _age_years(date_of_birth: date | None) -> int | None:
    if date_of_birth is None:
        return None
    return (date.today() - date_of_birth).days // 365
