"""Analysis persistence including lifecycle transitions and history queries.

History is paginated at the database level with a stable ordering
(created_at DESC, id DESC) and whitelisted filters only.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Analysis,
    AnalysisContext,
    AnalysisFeedback,
    AnalysisMedia,
    AnalysisObservation,
    AnalysisResult,
)
from app.domain.enums import AnalysisStatus
from app.schemas.analyses import AnalysisCreateRequest

_LOAD_OPTIONS = [
    selectinload(Analysis.media),
    selectinload(Analysis.context),
    selectinload(Analysis.observations),
    selectinload(Analysis.result),
    selectinload(Analysis.feedback),
]


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class AnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- Creation ---------------------------------------------------------
    async def create(
        self,
        *,
        user_id: uuid.UUID,
        dog_id: uuid.UUID,
        payload: AnalysisCreateRequest,
    ) -> Analysis:
        analysis = Analysis(
            dog_id=dog_id,
            user_id=user_id,
            status=AnalysisStatus.CREATED.value,
            input_type=payload.input_type.value,
            idempotency_key=payload.idempotency_key,
        )
        self._session.add(analysis)
        await self._session.flush()
        return analysis

    def add_media_source(self, analysis: Analysis, asset: AnalysisMedia) -> None:
        """Attach an immutable metadata snapshot of a media asset to analysis.

        The relationship column is set directly (never via `analysis.media`,
        which would trigger a lazy load that is forbidden in async sessions).
        """
        asset.analysis_id = analysis.id
        self._session.add(asset)

    def add_context(self, analysis: Analysis, context: AnalysisContext) -> None:
        analysis.context = context
        self._session.add(context)

    # --- Reads ------------------------------------------------------------
    async def get_by_id_and_user(
        self, analysis_id: uuid.UUID, user_id: uuid.UUID
    ) -> Analysis | None:
        stmt = (
            select(Analysis)
            .options(*_LOAD_OPTIONS)
            .where(Analysis.id == analysis_id, Analysis.user_id == user_id)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_idempotency(self, user_id: uuid.UUID, idempotency_key: str) -> Analysis | None:
        stmt = (
            select(Analysis)
            .options(*_LOAD_OPTIONS)
            .where(
                Analysis.user_id == user_id,
                Analysis.idempotency_key == idempotency_key,
            )
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    # --- Lifecycle --------------------------------------------------------
    async def queue(self, analysis: Analysis) -> None:
        analysis.status = AnalysisStatus.QUEUED.value
        await self._session.flush()

    async def start_processing(self, analysis: Analysis) -> None:
        analysis.status = AnalysisStatus.PROCESSING.value
        analysis.started_at = _utcnow()
        await self._session.flush()

    async def fail(self, analysis: Analysis, failure_code: str, message: str) -> None:
        analysis.status = AnalysisStatus.FAILED.value
        analysis.failure_code = failure_code
        analysis.failure_message = message
        analysis.completed_at = _utcnow()
        await self._session.flush()

    async def complete(
        self,
        analysis: Analysis,
        *,
        primary_behavior: str,
        confidence: float,
        secondary_behaviors: list[str],
        detected_audio_category: str | None,
        explanation: str,
        disclaimer: str,
        provider: str,
        model_name: str,
        model_version: str,
        is_placeholder: bool,
        observations: list[AnalysisObservation],
    ) -> None:
        analysis.status = AnalysisStatus.COMPLETED.value
        analysis.completed_at = _utcnow()
        result = AnalysisResult(
            analysis=analysis,
            primary_behavior=primary_behavior,
            confidence=confidence,
            secondary_behaviors=secondary_behaviors,
            detected_audio_category=detected_audio_category,
            explanation=explanation,
            disclaimer=disclaimer,
            provider=provider,
            model_name=model_name,
            model_version=model_version,
            is_placeholder=is_placeholder,
        )
        for observation in observations:
            observation.analysis = analysis
            self._session.add(observation)
        self._session.add(result)
        await self._session.flush()

    # --- History ----------------------------------------------------------
    async def has_analyses_for_dog(self, user_id: uuid.UUID, dog_id: uuid.UUID) -> bool:
        stmt = select(Analysis.id).where(Analysis.user_id == user_id, Analysis.dog_id == dog_id)
        return (await self._session.execute(stmt.limit(1))).first() is not None

    async def list_history(
        self,
        *,
        user_id: uuid.UUID,
        dog_id: uuid.UUID | None = None,
        behavior: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Analysis], int]:
        conditions = [Analysis.user_id == user_id]
        if dog_id is not None:
            conditions.append(Analysis.dog_id == dog_id)
        if behavior is not None:
            conditions.append(
                Analysis.id.in_(
                    select(AnalysisResult.analysis_id).where(
                        AnalysisResult.primary_behavior == behavior
                    )
                )
            )
        if date_from is not None:
            conditions.append(
                Analysis.created_at >= datetime.combine(date_from, time.min, tzinfo=UTC)
            )
        if date_to is not None:
            conditions.append(
                Analysis.created_at <= datetime.combine(date_to, time.max, tzinfo=UTC)
            )

        total = (
            await self._session.execute(select(func.count(Analysis.id)).where(*conditions))
        ).scalar_one()

        stmt = (
            select(Analysis)
            .options(*_LOAD_OPTIONS)
            .where(*conditions)
            .order_by(Analysis.created_at.desc(), Analysis.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list((await self._session.execute(stmt)).scalars())
        return items, total


class FeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        analysis: Analysis,
        user_id: uuid.UUID,
        verdict: str,
        predicted_behavior: str | None,
        corrected_behavior: str | None = None,
        comment: str | None = None,
    ) -> AnalysisFeedback:
        feedback = AnalysisFeedback(
            analysis_id=analysis.id,
            user_id=user_id,
            verdict=verdict,
            predicted_behavior=predicted_behavior,
            corrected_behavior=corrected_behavior,
            comment=comment,
        )
        self._session.add(feedback)
        await self._session.flush()
        return feedback
