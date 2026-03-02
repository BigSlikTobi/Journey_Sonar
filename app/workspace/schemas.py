"""Pydantic request/response schemas for the Workspace module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Workspace ---


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9\-]+$")
    settings: dict = Field(default_factory=dict)


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    settings: dict | None = None


class WorkspaceRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    name: str
    slug: str
    settings: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- API Keys ---


class ApiKeyCreate(BaseModel):
    label: str = Field(default="", max_length=255)
    scopes: list[str] = Field(default_factory=list)


class ApiKeyCreated(BaseModel):
    """Returned only on creation — includes the raw key (never stored)."""

    model_config = {"from_attributes": True}

    id: UUID
    prefix: str
    label: str
    scopes: list[str]
    raw_key: str  # Only available at creation time


class ApiKeyRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    prefix: str
    label: str
    scopes: list[str]
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
