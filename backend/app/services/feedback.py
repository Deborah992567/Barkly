"""Owner feedback service.

The original prediction is snapshotted when feedback is recorded and never
overwritten, so the feedback trail stays useful for future evaluation and
personalization.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.db.models import Analysis, AnalysisFeedback
from app.domain.enums import AnalysisStatus
from app.repositories.analyses import FeedbackRepository
from app.schemas.feedback import FeedbackCreate


class FeedbackService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._feedback = FeedbackRepository(session)

    async def submit(
        self, user_id, analysis: Analysis, payload: FeedbackCreate
    ) -> AnalysisFeedback:
        if analysis.status != AnalysisStatus.COMPLETED.value or analysis.result is None:
            raise AppError(
                ErrorCode.INVALID_OPERATION,
                "Feedback can only be submitted for a completed analysis.",
                status_code=409,
            )
        predicted = analysis.result.primary_behavior
        return await self._feedback.create(
            analysis=analysis,
            user_id=user_id,
            verdict=payload.verdict.value,
            predicted_behavior=predicted,
            corrected_behavior=(
                payload.corrected_behavior.value if payload.corrected_behavior else None
            ),
            comment=payload.comment,
        )
