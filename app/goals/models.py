"""SQLAlchemy models for the Goal Engine — schema: goals."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.types import GoalPriority, GoalStatus, GoalType, TargetDirection
from app.database import Base


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (
        Index("ix_goal_workspace_node", "workspace_id", "target_node_id"),
        {"schema": "goals"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    goal_type: Mapped[GoalType] = mapped_column(Enum(GoalType, schema="goals"), nullable=False)
    target_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    metric_definition: Mapped[dict] = mapped_column(JSONB, nullable=False)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    target_direction: Mapped[TargetDirection] = mapped_column(
        Enum(TargetDirection, schema="goals"), nullable=False
    )
    target_range: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    time_window: Mapped[str] = mapped_column(String(50), nullable=False)  # ISO 8601 duration
    priority: Mapped[GoalPriority] = mapped_column(
        Enum(GoalPriority, schema="goals"), default=GoalPriority.MEDIUM
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class GoalSnapshot(Base):
    __tablename__ = "goal_snapshots"
    __table_args__ = (
        Index("ix_snapshot_goal_time", "goal_id", "snapshot_at"),
        {"schema": "goals"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    goal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    gap: Mapped[float] = mapped_column(Float, nullable=False)
    gap_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[GoalStatus] = mapped_column(Enum(GoalStatus, schema="goals"), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    computation_details: Mapped[dict] = mapped_column(JSONB, default=dict)
