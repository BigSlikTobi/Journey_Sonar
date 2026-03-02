"""Shared Pydantic schemas used across module boundaries."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Pagination(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)


class TimeRange(BaseModel):
    start: datetime
    end: datetime


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    offset: int
    limit: int


class WorkspaceContext(BaseModel):
    """Injected into every request after auth middleware resolves the workspace."""

    workspace_id: UUID
    scopes: list[str] = Field(default_factory=list)
