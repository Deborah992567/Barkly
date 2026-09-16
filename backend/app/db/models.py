"""SQLAlchemy ORM models for BARKLY.

Entities: users, dogs, analyses, analysis_media, analysis_context,
analysis_observations, analysis_results, analysis_feedback.

Behavioral state, audio category, statuses and media types are stored as string
columns (not native enums) so the controlled vocabulary can evolve without a
complete database rewrite.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    dogs: Mapped[list[Dog]] = relationship(back_populates="owner")
    analyses: Mapped[list[Analysis]] = relationship(
        back_populates="owner", foreign_keys="Analysis.user_id"
    )


class Dog(Base):
    __tablename__ = "dogs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    breed: Mapped[str | None] = mapped_column(String(120))
    sex: Mapped[str | None] = mapped_column(String(20))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    owner: Mapped[User] = relationship(back_populates="dogs")
    analyses: Mapped[list[Analysis]] = relationship(back_populates="dog")

    __table_args__ = (Index("ix_dogs_owner_id_name", "owner_id", "name"),)


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    dog_id: Mapped[UUID] = mapped_column(ForeignKey("dogs.id", ondelete="RESTRICT"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="CREATED", index=True)
    input_type: Mapped[str] = mapped_column(String(20))
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    failure_code: Mapped[str | None] = mapped_column(String(40))
    failure_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    dog: Mapped[Dog] = relationship(back_populates="analyses")
    owner: Mapped[User] = relationship(back_populates="analyses", foreign_keys=[user_id])
    media: Mapped[list[AnalysisMedia]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )
    context: Mapped[AnalysisContext | None] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", uselist=False
    )
    observations: Mapped[list[AnalysisObservation]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )
    result: Mapped[AnalysisResult | None] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", uselist=False
    )
    feedback: Mapped[list[AnalysisFeedback]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_analyses_dog_created", "dog_id", "created_at"),
        Index("ix_analyses_user_created", "user_id", "created_at"),
        Index("ix_analyses_status_created", "status", "created_at"),
    )


class AnalysisMedia(Base):
    __tablename__ = "analysis_media"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), index=True
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="RESTRICT"), index=True
    )
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    media_type: Mapped[str] = mapped_column(String(20))
    original_filename: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(120))
    file_size: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    media_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    storage_reference: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    analysis: Mapped[Analysis | None] = relationship(back_populates="media")


class AnalysisContext(Base):
    __tablename__ = "analysis_context"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, index=True
    )
    owner_presence: Mapped[str | None] = mapped_column(String(20))
    activity_state: Mapped[str | None] = mapped_column(String(20))
    time_of_day: Mapped[str | None] = mapped_column(String(20))
    recent_feeding: Mapped[bool | None] = mapped_column(Boolean)
    recent_walk: Mapped[bool | None] = mapped_column(Boolean)
    recent_play: Mapped[bool | None] = mapped_column(Boolean)
    presence_of_strangers: Mapped[bool | None] = mapped_column(Boolean)
    presence_of_other_animals: Mapped[bool | None] = mapped_column(Boolean)
    recent_stressful_event: Mapped[bool | None] = mapped_column(Boolean)
    location_category: Mapped[str | None] = mapped_column(String(60))
    notes: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[Analysis] = relationship(back_populates="context")


class AnalysisObservation(Base):
    __tablename__ = "analysis_observations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)

    analysis: Mapped[Analysis] = relationship(back_populates="observations")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, index=True
    )
    primary_behavior: Mapped[str] = mapped_column(String(40))
    confidence: Mapped[float] = mapped_column(Float)
    secondary_behaviors: Mapped[list[Any]] = mapped_column(JSON, default=list)
    detected_audio_category: Mapped[str | None] = mapped_column(String(20))
    explanation: Mapped[str] = mapped_column(Text)
    disclaimer: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(80))
    model_name: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str] = mapped_column(String(40))
    is_placeholder: Mapped[bool] = mapped_column(Boolean, default=False)
    # Phase 4 tracability: which model artifacts, datasets and system versions
    # produced this result, plus the signal availability snapshot.
    audio_model_name: Mapped[str | None] = mapped_column(String(120))
    audio_model_version: Mapped[str | None] = mapped_column(String(80))
    vision_model_name: Mapped[str | None] = mapped_column(String(120))
    vision_model_version: Mapped[str | None] = mapped_column(String(80))
    preprocessing_version: Mapped[str | None] = mapped_column(String(80))
    dataset_version: Mapped[str | None] = mapped_column(String(120))
    fusion_version: Mapped[str | None] = mapped_column(String(80))
    interpretation_version: Mapped[str | None] = mapped_column(String(80))
    inference_latency_ms: Mapped[int | None] = mapped_column(Integer)
    is_insufficient_evidence: Mapped[bool] = mapped_column(Boolean, default=False)
    signals_available: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    analysis: Mapped[Analysis] = relationship(back_populates="result")


class AnalysisFeedback(Base):
    __tablename__ = "analysis_feedback"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    verdict: Mapped[str] = mapped_column(String(20))
    predicted_behavior: Mapped[str | None] = mapped_column(String(40))
    corrected_behavior: Mapped[str | None] = mapped_column(String(40))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    analysis: Mapped[Analysis] = relationship(back_populates="feedback")


class MediaAsset(Base):
    """Uploaded media not yet attached to an analysis (owned by a user)."""

    __tablename__ = "media_assets"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    media_type: Mapped[str] = mapped_column(String(20))
    original_filename: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(120))
    file_size: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    media_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    storage_reference: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (Index("ix_media_assets_owner_created", "owner_id", "created_at"),)
