"""SQLAlchemy models for the Sonar Engine — schema: sonar."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.types import ReportType, ScoreType
from app.database import Base


class NodeScore(Base):
    __tablename__ = "node_scores"
    __table_args__ = (
        Index("ix_score_node_type_time", "workspace_id", "node_id", "score_type", "computed_at"),
        {"schema": "sonar"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    score_type: Mapped[ScoreType] = mapped_column(Enum(ScoreType, schema="sonar"), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    components: Mapped[dict] = mapped_column(JSONB, default=dict)
    time_window: Mapped[str] = mapped_column(String(50), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SonarReport(Base):
    __tablename__ = "sonar_reports"
    __table_args__ = {"schema": "sonar"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType, schema="sonar"), nullable=False
    )
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict)
    results: Mapped[dict] = mapped_column(JSONB, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FocusRecommendation(Base):
    __tablename__ = "focus_recommendations"
    __table_args__ = {"schema": "sonar"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[dict] = mapped_column(JSONB, default=dict)
    related_goal_ids: Mapped[list] = mapped_column(JSONB, default=list)
    recommended_actions: Mapped[list] = mapped_column(JSONB, default=list)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
