"""HTTP endpoints for the Data Ingestion Pipeline."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import WorkspaceContext
from app.database import get_session
from app.ingestion.schemas import (
    DataSourceCreate,
    DataSourceRead,
    DataSourceUpdate,
    EventBatchIngest,
    EventIngest,
    NormalizedEventRead,
)
from app.ingestion.service import IngestionService
from app.workspace.dependencies import require_workspace

router = APIRouter()
_service = IngestionService()


# --- DataSource endpoints ---


@router.post("/sources", response_model=DataSourceRead, status_code=201)
async def create_source(
    data: DataSourceCreate,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> DataSourceRead:
    source = await _service.create_source(session, ctx.workspace_id, data)
    await session.commit()
    return DataSourceRead.model_validate(source)


@router.get("/sources", response_model=list[DataSourceRead])
async def list_sources(
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> list[DataSourceRead]:
    sources = await _service.list_sources(session, ctx.workspace_id)
    return [DataSourceRead.model_validate(s) for s in sources]


@router.patch("/sources/{source_id}", response_model=DataSourceRead)
async def update_source(
    source_id: UUID,
    data: DataSourceUpdate,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> DataSourceRead:
    source = await _service.update_source(session, ctx.workspace_id, source_id, data)
    await session.commit()
    return DataSourceRead.model_validate(source)


# --- Event ingestion endpoints ---


@router.post("/sources/{source_id}/events", response_model=NormalizedEventRead, status_code=201)
async def ingest_event(
    source_id: UUID,
    data: EventIngest,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> NormalizedEventRead:
    normalized = await _service.ingest_event(session, ctx.workspace_id, source_id, data)
    await session.commit()
    return NormalizedEventRead.model_validate(normalized)


@router.post(
    "/sources/{source_id}/events/batch",
    response_model=list[NormalizedEventRead],
    status_code=201,
)
async def ingest_batch(
    source_id: UUID,
    data: EventBatchIngest,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> list[NormalizedEventRead]:
    results = await _service.ingest_batch(session, ctx.workspace_id, source_id, data.events)
    await session.commit()
    return [NormalizedEventRead.model_validate(r) for r in results]
