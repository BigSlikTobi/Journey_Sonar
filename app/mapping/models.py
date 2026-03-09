"""SQLAlchemy models for the Mapping Engine."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.types import SignalType, SuggestionStatus
from app.database import Base


class MappingRule(Base):
    __tablename__ = "mapping_rules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    target_node_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    conditions: Mapped[dict] = mapped_column(JSON, nullable=False)
    signal_type: Mapped[SignalType] = mapped_column(Enum(SignalType), nullable=False)
    signal_weight: Mapped[float] = mapped_column(Float, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MappedSignal(Base):
    __tablename__ = "mapped_signals"
    __table_args__ = (
        Index("ix_signal_node_time", "workspace_id", "node_id", "event_occurred_at"),
        Index("ix_signal_actor_time", "workspace_id", "actor_id", "event_occurred_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    normalized_event_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    mapping_rule_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    node_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    signal_type: Mapped[SignalType] = mapped_column(Enum(SignalType), nullable=False)
    signal_weight: Mapped[float] = mapped_column(Float, default=1.0)
    signal_value: Mapped[float] = mapped_column(Float, nullable=False)
    mapped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    event_occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AutoMappingSuggestion(Base):
    __tablename__ = "auto_mapping_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    normalized_event_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    suggested_node_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(String(1000), default="")
    status: Mapped[SuggestionStatus] = mapped_column(
        Enum(SuggestionStatus), default=SuggestionStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
