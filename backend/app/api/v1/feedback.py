"""Owner feedback on an analysis result.

Ownership is enforced: the referenced analysis must belong to the
authenticated user. The original prediction is preserved on every feedback row.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.serializers import feedback_to_read
from app.core.errors import ErrorCode, not_found_error
from app.db.models import User
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.repositories.analyses import AnalysisRepository
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from app.services.feedback import FeedbackService

router = APIRouter(tags=["feedback"])


@router.post(
    "/{analysis_id}/feedback",
    response_model=FeedbackRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit confirmation or correction for an analysis",
)
async def submit_feedback(
    analysis_id: uuid.UUID,
    payload: FeedbackCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> FeedbackRead:
    analysis = await AnalysisRepository(session).get_by_id_and_user(analysis_id, user.id)
    if analysis is None:
        raise not_found_error(
            ErrorCode.ANALYSIS_NOT_FOUND, "The requested analysis could not be found."
        )
    feedback = await FeedbackService(session).submit(user.id, analysis, payload)
    await session.commit()
    return feedback_to_read(feedback)
