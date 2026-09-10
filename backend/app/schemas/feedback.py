"""Owner feedback on analysis predictions.

The original prediction is always preserved separately; feedback never
overwrites it, enabling later personalization and evaluation.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.enums import BehaviorState, FeedbackVerdict
from app.schemas.common import APIModel


class FeedbackCreate(APIModel):
    verdict: FeedbackVerdict
    corrected_behavior: BehaviorState | None = None
    comment: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _corrected_requires_correction(self) -> FeedbackCreate:
        if self.verdict == FeedbackVerdict.CORRECTED and self.corrected_behavior is None:
            raise ValueError("corrected_behavior is required for a CORRECTED verdict.")
        if self.verdict == FeedbackVerdict.CONFIRMED and self.corrected_behavior is not None:
            raise ValueError("corrected_behavior must not be set for a CONFIRMED verdict.")
        return self


class FeedbackRead(APIModel):
    id: UUID
    analysis_id: UUID
    verdict: FeedbackVerdict
    predicted_behavior: BehaviorState | None
    corrected_behavior: BehaviorState | None
    comment: str | None
    created_at: datetime
