"""Explicit ORM → schema serializers for API responses.

Services return domain/ORM objects; this module owns the mapping to stable
Pydantic response shapes so the contract never exposes database internals.
"""

from __future__ import annotations

from app.db.models import (
    Analysis,
    AnalysisFeedback,
    AnalysisMedia,
    Dog,
    MediaAsset,
)
from app.domain.enums import AnalysisStatus
from app.schemas.analyses import (
    AnalysisRead,
    AnalysisResultRead,
    AnalysisStatusRead,
    FailureRead,
    ObservationRead,
)
from app.schemas.dogs import DogRead
from app.schemas.feedback import FeedbackRead
from app.schemas.media import MediaAssetRead


def dog_to_read(dog: Dog) -> DogRead:
    return DogRead(
        id=dog.id,
        name=dog.name,
        breed=dog.breed,
        sex=dog.sex,
        date_of_birth=dog.date_of_birth,
        notes=dog.notes,
        created_at=dog.created_at,
        updated_at=dog.updated_at,
    )


def _media_snapshot_to_read(media: AnalysisMedia) -> MediaAssetRead:
    return MediaAssetRead(
        media_id=media.asset_id or media.id,
        media_type=media.media_type,
        original_filename=media.original_filename,
        mime_type=media.mime_type,
        file_size=media.file_size,
        duration_ms=media.duration_ms,
        media_metadata=None,
        created_at=media.created_at,
    )


def _result_to_read(result, observations: list) -> AnalysisResultRead:
    observation_reads = [
        ObservationRead(category=observation.category, description=observation.description)
        for observation in observations
    ]
    return AnalysisResultRead(
        primary_behavior=result.primary_behavior,
        confidence=result.confidence,
        secondary_behaviors=result.secondary_behaviors,
        detected_audio_category=result.detected_audio_category,
        observations=observation_reads,
        explanation=result.explanation,
        disclaimer=result.disclaimer,
        provider=result.provider,
        model_name=result.model_name,
        model_version=result.model_version,
        is_placeholder=result.is_placeholder,
        generated_at=result.generated_at,
        audio_model_name=result.audio_model_name,
        audio_model_version=result.audio_model_version,
        vision_model_name=result.vision_model_name,
        vision_model_version=result.vision_model_version,
        preprocessing_version=result.preprocessing_version,
        dataset_version=result.dataset_version,
        fusion_version=result.fusion_version,
        interpretation_version=result.interpretation_version,
        inference_latency_ms=result.inference_latency_ms,
        is_insufficient_evidence=result.is_insufficient_evidence,
        signals_available=result.signals_available,
    )


def analysis_to_status_read(analysis: Analysis) -> AnalysisStatusRead:
    failure = None
    if analysis.failure_code:
        failure = FailureRead(
            code=analysis.failure_code,
            message=analysis.failure_message or "",
        )
    result = _result_to_read(analysis.result, analysis.observations) if analysis.result else None
    return AnalysisStatusRead(
        analysis_id=analysis.id,
        dog_id=analysis.dog_id,
        status=AnalysisStatus(analysis.status),
        input_type=analysis.input_type,
        created_at=analysis.created_at,
        started_at=analysis.started_at,
        completed_at=analysis.completed_at,
        failure=failure,
        result=result,
    )


def analysis_to_read(analysis: Analysis) -> AnalysisRead:
    status_read = analysis_to_status_read(analysis)
    from app.schemas.context import AnalysisContextRead

    context = None
    if analysis.context is not None:
        context = AnalysisContextRead(
            owner_presence=analysis.context.owner_presence,
            activity_state=analysis.context.activity_state,
            time_of_day=analysis.context.time_of_day,
            recent_feeding=analysis.context.recent_feeding,
            recent_walk=analysis.context.recent_walk,
            recent_play=analysis.context.recent_play,
            presence_of_strangers=analysis.context.presence_of_strangers,
            presence_of_other_animals=analysis.context.presence_of_other_animals,
            recent_stressful_event=analysis.context.recent_stressful_event,
            location_category=analysis.context.location_category,
            notes=analysis.context.notes,
        )
    return AnalysisRead(
        **status_read.model_dump(),
        media=[_media_snapshot_to_read(m) for m in analysis.media],
        context=context,
    )


def media_asset_to_read(asset: MediaAsset) -> MediaAssetRead:
    return MediaAssetRead(
        media_id=asset.id,
        media_type=asset.media_type,
        original_filename=asset.original_filename,
        mime_type=asset.mime_type,
        file_size=asset.file_size,
        duration_ms=asset.duration_ms,
        media_metadata=asset.media_metadata,
        created_at=asset.created_at,
    )


def feedback_to_read(feedback: AnalysisFeedback) -> FeedbackRead:
    return FeedbackRead(
        id=feedback.id,
        analysis_id=feedback.analysis_id,
        verdict=feedback.verdict,
        predicted_behavior=feedback.predicted_behavior,
        corrected_behavior=feedback.corrected_behavior,
        comment=feedback.comment,
        created_at=feedback.created_at,
    )
