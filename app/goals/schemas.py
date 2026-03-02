"""Pydantic request/response schemas for the Goal Engine."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.common.types import GoalPriority, GoalStatus, GoalType, TargetDirection


# --- Goal ---


class GoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    goal_type: GoalType
    target_node_id: UUID
    metric_definition: dict
    target_value: float
    target_direction: TargetDirection
    target_range: dict | None = None
    time_window: str = "P30D"
    priority: GoalPriority = GoalPriority.MEDIUM


class GoalUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    target_value: float | None = None
    target_direction: TargetDirection | None = None
    target_range: dict | None = None
    time_window: str | None = None
    priority: GoalPriority | None = None
    is_active: bool | None = None


class GoalRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    goal_type: GoalType
    target_node_id: UUID
    metric_definition: dict
    target_value: float
    target_direction: TargetDirection
    target_range: dict | None
    time_window: str
    priority: GoalPriority
    is_active: bool
    created_at: datetime


# --- GoalSnapshot ---


class GoalSnapshotRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    goal_id: UUID
    current_value: float
    target_value: float
    gap: float
    gap_percentage: float
    status: GoalStatus
    snapshot_at: datetime
    computation_details: dict


# --- Summary ---


class GoalsSummary(BaseModel):
    on_track: int = 0
    at_risk: int = 0
    off_track: int = 0
    exceeded: int = 0
    total: int = 0
