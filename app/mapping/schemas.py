"""Pydantic request/response schemas for the Mapping Engine."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.common.types import SignalType, SuggestionStatus


# --- MappingRule ---


class MappingRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    target_node_id: UUID
    priority: int = 0
    conditions: dict
    signal_type: SignalType
    signal_weight: float = 1.0


class MappingRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    target_node_id: UUID | None = None
    priority: int | None = None
    conditions: dict | None = None
    signal_type: SignalType | None = None
    signal_weight: float | None = None
    is_active: bool | None = None


class MappingRuleRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    target_node_id: UUID
    priority: int
    conditions: dict
    signal_type: SignalType
    signal_weight: float
    is_active: bool
    created_at: datetime


# --- MappedSignal ---


class MappedSignalRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    normalized_event_id: UUID
    mapping_rule_id: UUID
    node_id: UUID
    actor_id: str | None
    signal_type: SignalType
    signal_weight: float
    signal_value: float
    mapped_at: datetime
    event_occurred_at: datetime


# --- Signal Aggregation (for Sonar) ---


class SignalBucket(BaseModel):
    """Time-bucketed signal aggregation."""

    period_start: datetime
    period_end: datetime
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    total_value: float = 0.0
    distinct_actors: int = 0


# --- AutoMappingSuggestion ---


class AutoMappingSuggestionRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    normalized_event_id: UUID
    suggested_node_id: UUID
    confidence: float
    reasoning: str
    status: SuggestionStatus
    created_at: datetime
