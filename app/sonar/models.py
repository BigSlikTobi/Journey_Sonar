"""SQLAlchemy models for the Sonar Engine."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.types import ReportType, ScoreType
from app.database import Base


class NodeScore(Base):
    __tablename__ = "node_scores"
    __table_args__ = (
        Index("ix_score_node_type_time", "workspace_id", "node_id", "score_type", "computed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    node_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    score_type: Mapped[ScoreType] = mapped_column(Enum(ScoreType), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    components: Mapped[dict] = mapped_column(JSON, default=dict)
    time_window: Mapped[str] = mapped_column(String(50), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SonarReport(Base):
    __tablename__ = "sonar_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    results: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FocusRecommendation(Base):
    __tablename__ = "focus_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    node_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[dict] = mapped_column(JSON, default=dict)
    related_goal_ids: Mapped[list] = mapped_column(JSON, default=list)
    recommended_actions: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
