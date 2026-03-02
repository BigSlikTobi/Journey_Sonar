"""HTTP endpoints for the Journey Engine."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import WorkspaceContext
from app.database import get_session
from app.journey.schemas import (
    EdgeCreate,
    EdgeRead,
    NodeCreate,
    NodeMatch,
    NodeRead,
    NodeUpdate,
)
from app.journey.service import JourneyService
from app.workspace.dependencies import require_workspace

router = APIRouter()
_service = JourneyService()


# --- Node endpoints ---


@router.post("/nodes", response_model=NodeRead, status_code=201)
async def create_node(
    data: NodeCreate,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> NodeRead:
    node = await _service.create_node(session, ctx.workspace_id, data)
    await session.commit()
    return NodeRead.model_validate(node)


@router.get("/nodes/{node_id}", response_model=NodeRead)
async def get_node(
    node_id: UUID,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> NodeRead:
    node = await _service.get_node(session, ctx.workspace_id, node_id)
    return NodeRead.model_validate(node)


@router.patch("/nodes/{node_id}", response_model=NodeRead)
async def update_node(
    node_id: UUID,
    data: NodeUpdate,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> NodeRead:
    node = await _service.update_node(session, ctx.workspace_id, node_id, data)
    await session.commit()
    return NodeRead.model_validate(node)


@router.delete("/nodes/{node_id}", status_code=204)
async def delete_node(
    node_id: UUID,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> None:
    await _service.delete_node(session, ctx.workspace_id, node_id)
    await session.commit()


@router.get("/nodes/{node_id}/sub-journey", response_model=list[NodeRead])
async def get_sub_journey(
    node_id: UUID,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> list[NodeRead]:
    children = await _service.get_sub_journey(session, ctx.workspace_id, node_id)
    return [NodeRead.model_validate(c) for c in children]


@router.get("/nodes/{node_id}/ancestors")
async def get_ancestors(
    node_id: UUID,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await _service.get_ancestor_chain(session, ctx.workspace_id, node_id)


@router.get("/nodes/match-inputs", response_model=list[NodeMatch])
async def match_inputs(
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
    payload: str = Query(..., description="JSON-encoded data payload to match"),
) -> list[NodeMatch]:
    import json
    data_payload = json.loads(payload)
    return await _service.match_node_by_input(session, ctx.workspace_id, data_payload)


# --- Edge endpoints ---


@router.post("/edges", response_model=EdgeRead, status_code=201)
async def create_edge(
    data: EdgeCreate,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> EdgeRead:
    edge = await _service.create_edge(session, ctx.workspace_id, data)
    await session.commit()
    return EdgeRead.model_validate(edge)


@router.get("/edges", response_model=list[EdgeRead])
async def get_edges(
    source: UUID = Query(..., description="Source node ID"),
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> list[EdgeRead]:
    edges = await _service.get_outgoing_edges(session, ctx.workspace_id, source)
    return [EdgeRead.model_validate(e) for e in edges]


@router.delete("/edges/{edge_id}", status_code=204)
async def delete_edge(
    edge_id: UUID,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> None:
    await _service.delete_edge(session, ctx.workspace_id, edge_id)
    await session.commit()
