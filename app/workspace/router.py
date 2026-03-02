"""HTTP endpoints for the Workspace module."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.workspace.schemas import (
    ApiKeyCreate,
    ApiKeyCreated,
    WorkspaceCreate,
    WorkspaceRead,
    WorkspaceUpdate,
)
from app.workspace.service import WorkspaceService

router = APIRouter()
_service = WorkspaceService()


@router.post("", response_model=WorkspaceRead, status_code=201)
async def create_workspace(
    data: WorkspaceCreate,
    session: AsyncSession = Depends(get_session),
) -> WorkspaceRead:
    ws = await _service.create_workspace(session, data)
    await session.commit()
    return WorkspaceRead.model_validate(ws)


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    workspace_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> WorkspaceRead:
    ws = await _service.get_workspace(session, workspace_id)
    return WorkspaceRead.model_validate(ws)


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    session: AsyncSession = Depends(get_session),
) -> WorkspaceRead:
    ws = await _service.update_workspace(session, workspace_id, data)
    await session.commit()
    return WorkspaceRead.model_validate(ws)


@router.post("/{workspace_id}/api-keys", response_model=ApiKeyCreated, status_code=201)
async def create_api_key(
    workspace_id: UUID,
    data: ApiKeyCreate,
    session: AsyncSession = Depends(get_session),
) -> ApiKeyCreated:
    api_key, raw_key = await _service.create_api_key(session, workspace_id, data)
    await session.commit()
    return ApiKeyCreated(
        id=api_key.id,
        prefix=api_key.prefix,
        label=api_key.label,
        scopes=api_key.scopes,
        raw_key=raw_key,
    )
