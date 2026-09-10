"""Structured context signals for an analysis.

Every field is optional; users are never forced to answer context questions.
Coarse categories only — no GPS-level precision is collected.
"""

from __future__ import annotations

from pydantic import Field

from app.domain.enums import ActivityState, OwnerPresence, TimeOfDayCategory
from app.schemas.common import APIModel


class AnalysisContextCreate(APIModel):
    owner_presence: OwnerPresence | None = None
    activity_state: ActivityState | None = None
    time_of_day: TimeOfDayCategory | None = None
    recent_feeding: bool | None = None
    recent_walk: bool | None = None
    recent_play: bool | None = None
    presence_of_strangers: bool | None = None
    presence_of_other_animals: bool | None = None
    recent_stressful_event: bool | None = None
    location_category: str | None = Field(default=None, max_length=60)
    notes: str | None = Field(default=None, max_length=2000)


class AnalysisContextRead(AnalysisContextCreate):
    pass
