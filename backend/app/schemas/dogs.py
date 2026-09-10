"""Dog profile schemas.

Breed, sex and date-of-birth are optional: owners are never forced to provide
information they do not know.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.enums import Sex
from app.schemas.common import APIModel


class DogCreate(APIModel):
    name: str = Field(min_length=1, max_length=120)
    breed: str | None = Field(default=None, max_length=120)
    sex: Sex | None = None
    date_of_birth: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class DogUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    breed: str | None = Field(default=None, max_length=120)
    sex: Sex | None = None
    date_of_birth: date | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _prevent_empty_update(self) -> DogUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self


class DogRead(APIModel):
    id: UUID
    name: str
    breed: str | None
    sex: Sex | None
    date_of_birth: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    @property
    def age_years(self) -> int | None:
        if self.date_of_birth is None:
            return None
        return (date.today() - self.date_of_birth).days // 365


class DogSummary(APIModel):
    id: UUID
    name: str
    breed: str | None
    sex: Sex | None
