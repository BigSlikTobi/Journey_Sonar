"""Pydantic request/response schemas for the Sonar Engine."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.common.types import ScoreType


class NodeScoreRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    node_id: UUID
    score_type: ScoreType
    value: float
    components: dict
    time_window: str
    computed_at: datetime


class FocusRecommendationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    node_id: UUID
    rank: int
    composite_score: float
    reasoning: dict
    related_goal_ids: list[UUID]
    recommended_actions: list[str]
    generated_at: datetime


class FocusMapRequest(BaseModel):
    top_n: int = Field(default=10, ge=1, le=100)
    scope_node_id: UUID | None = None
    time_window: str = "P7D"
