"""Pydantic request/response schemas for the Journey Engine."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.common.types import NodeType


# --- Node ---


class NodeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: NodeType
    parent_node_id: UUID | None = None
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    position: int = 0


class NodeUpdate(BaseModel):
    name: str | None = None
    type: NodeType | None = None
    parent_node_id: UUID | None = None
    input_schema: dict | None = None
    output_schema: dict | None = None
    metadata: dict | None = None
    position: int | None = None


class NodeRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    name: str
    type: NodeType
    parent_node_id: UUID | None
    input_schema: dict
    output_schema: dict
    metadata: dict = Field(validation_alias="metadata_")
    position: int
    created_at: datetime
    updated_at: datetime


class NodeMatch(BaseModel):
    """Returned by match-inputs: a node whose input_schema matched the payload."""

    node_id: UUID
    node_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    matched_fields: list[str]


# --- Edge ---


class EdgeCreate(BaseModel):
    source_node_id: UUID
    target_node_id: UUID
    condition: dict | None = None
    is_fallback: bool = False
    weight: float = 1.0
    metadata: dict = Field(default_factory=dict)


class EdgeRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    source_node_id: UUID
    target_node_id: UUID
    condition: dict | None
    is_fallback: bool
    weight: float
    created_at: datetime


# --- Tree ---


class NodeTree(BaseModel):
    """Recursive tree representation of a node and all descendants."""

    node: NodeRead
    children: list[NodeTree] = Field(default_factory=list)
    edges: list[EdgeRead] = Field(default_factory=list)
