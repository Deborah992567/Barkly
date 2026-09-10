"""Analysis history with database-side pagination and whitelisted filters."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.serializers import analysis_to_read
from app.core.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.domain.enums import BehaviorState
from app.repositories.analyses import AnalysisRepository
from app.schemas.history import HistoryResponse

router = APIRouter(tags=["history"])


@router.get("", response_model=HistoryResponse, summary="List analysis history")
async def list_history(
    dog_id: uuid.UUID | None = Query(default=None, description="Filter by dog"),
    behavior: BehaviorState | None = Query(default=None, description="Filter by primary behavior"),
    date_from: date | None = Query(default=None, description="Inclusive start date"),
    date_to: date | None = Query(default=None, description="Inclusive end date"),
    page: int = Query(default=1, ge=1, description="1-based page number"),
    page_size: int = Query(
        default=None,
        ge=1,
        description="Results per page (bounded by MAX_PAGE_SIZE)",
    ),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> HistoryResponse:
    settings = get_settings()
    page_size = page_size or settings.default_page_size
    page_size = min(page_size, settings.max_page_size)

    repository = AnalysisRepository(session)
    items, total = await repository.list_history(
        user_id=user.id,
        dog_id=dog_id,
        behavior=behavior.value if behavior else None,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return HistoryResponse(
        items=[analysis_to_read(analysis) for analysis in items],
        page=page,
        page_size=page_size,
        total=total,
        has_next=(page * page_size) < total,
    )
