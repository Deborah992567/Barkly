"""Pagination and history schemas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

from app.schemas.analyses import AnalysisRead

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    has_next: bool


class HistoryResponse(Page[AnalysisRead]):
    pass
