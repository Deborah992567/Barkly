"""Analysis endpoints: create and retrieve analysis records.

The lifecycle is explicit (CREATED → QUEUED → PROCESSING → COMPLETED/FAILED)
and returned as status so clients never infer state from missing fields.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.serializers import analysis_to_read
from app.core.errors import ErrorCode, not_found_error
from app.db.models import User
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.repositories.analyses import AnalysisRepository
from app.schemas.analyses import AnalysisCreateRequest, AnalysisRead
from app.services.analyses import AnalysisService

router = APIRouter(tags=["analyses"])


@router.post(
    "",
    response_model=AnalysisRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create and run an analysis",
)
async def create_analysis(
    payload: AnalysisCreateRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnalysisRead:
    analysis = await AnalysisService(session).create(user.id, payload)
    await session.commit()
    return analysis_to_read(analysis)


@router.get(
    "/{analysis_id}",
    response_model=AnalysisRead,
    summary="Get an analysis and its current status",
)
async def get_analysis(
    analysis_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnalysisRead:
    analysis = await AnalysisRepository(session).get_by_id_and_user(analysis_id, user.id)
    if analysis is None:
        raise not_found_error(
            ErrorCode.ANALYSIS_NOT_FOUND, "The requested analysis could not be found."
        )
    return analysis_to_read(analysis)
