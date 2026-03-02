"""Pydantic request/response schemas for the Data Ingestion Pipeline."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.common.types import ProcessingStatus, SourceType


# --- DataSource ---


class DataSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_type: SourceType
    config: dict = Field(default_factory=dict)
    normalization_rules: dict = Field(default_factory=dict)


class DataSourceUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None
    normalization_rules: dict | None = None
    is_active: bool | None = None


class DataSourceRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    name: str
    source_type: SourceType
    config: dict
    normalization_rules: dict
    is_active: bool
    created_at: datetime


# --- Events ---


class EventIngest(BaseModel):
    """Raw event payload sent by external source."""

    external_id: str | None = None
    payload: dict
    occurred_at: datetime | None = None


class EventBatchIngest(BaseModel):
    events: list[EventIngest] = Field(..., min_length=1, max_length=1000)


class NormalizedEventRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    raw_event_id: UUID
    source_id: UUID
    event_type: str
    actor_id: str | None
    properties: dict
    occurred_at: datetime
    processed_at: datetime
    processing_status: ProcessingStatus
    classification: dict | None


# --- Classification ---


class Classification(BaseModel):
    intent: str
    sentiment: float = Field(ge=-1.0, le=1.0)
    topics: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_entities: dict = Field(default_factory=dict)
