"""add phase 4 analysis result traceability columns

Revision ID: d1e2f3a4b5c6
Revises: b0b9c6b12587
Create Date: 2026-09-16 06:40:00.000000

Adds model/artifact traceability, signal availability, latency, and the
insufficient-evidence flag to analysis_results so every completed analysis
records exactly which artifacts produced it and how much evidence was used.
All new columns are nullable or defaulted; existing rows remain valid.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: str | None = "b0b9c6b12587"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("analysis_results", sa.Column("audio_model_name", sa.String(length=120), nullable=True))
    op.add_column("analysis_results", sa.Column("audio_model_version", sa.String(length=80), nullable=True))
    op.add_column("analysis_results", sa.Column("vision_model_name", sa.String(length=120), nullable=True))
    op.add_column("analysis_results", sa.Column("vision_model_version", sa.String(length=80), nullable=True))
    op.add_column("analysis_results", sa.Column("preprocessing_version", sa.String(length=80), nullable=True))
    op.add_column("analysis_results", sa.Column("dataset_version", sa.String(length=120), nullable=True))
    op.add_column("analysis_results", sa.Column("fusion_version", sa.String(length=80), nullable=True))
    op.add_column("analysis_results", sa.Column("interpretation_version", sa.String(length=80), nullable=True))
    op.add_column("analysis_results", sa.Column("inference_latency_ms", sa.Integer(), nullable=True))
    op.add_column("analysis_results", sa.Column("is_insufficient_evidence", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("analysis_results", sa.Column("signals_available", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("analysis_results", "signals_available")
    op.drop_column("analysis_results", "is_insufficient_evidence")
    op.drop_column("analysis_results", "inference_latency_ms")
    op.drop_column("analysis_results", "interpretation_version")
    op.drop_column("analysis_results", "fusion_version")
    op.drop_column("analysis_results", "dataset_version")
    op.drop_column("analysis_results", "preprocessing_version")
    op.drop_column("analysis_results", "vision_model_version")
    op.drop_column("analysis_results", "vision_model_name")
    op.drop_column("analysis_results", "audio_model_version")
    op.drop_column("analysis_results", "audio_model_name")
