"""HTTP endpoints for the Mapping Engine."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import WorkspaceContext
from app.database import get_session
from app.mapping.schemas import (
    MappedSignalRead,
    MappingRuleCreate,
    MappingRuleRead,
    MappingRuleUpdate,
)
from app.mapping.service import MappingService
from app.workspace.dependencies import require_workspace

router = APIRouter()
_service = MappingService()


# --- Rule endpoints ---


@router.post("/rules", response_model=MappingRuleRead, status_code=201)
async def create_rule(
    data: MappingRuleCreate,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> MappingRuleRead:
    rule = await _service.create_rule(session, ctx.workspace_id, data)
    await session.commit()
    return MappingRuleRead.model_validate(rule)


@router.get("/rules", response_model=list[MappingRuleRead])
async def list_rules(
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
    node_id: UUID | None = Query(default=None),
) -> list[MappingRuleRead]:
    rules = await _service.list_rules(session, ctx.workspace_id, node_id)
    return [MappingRuleRead.model_validate(r) for r in rules]


@router.patch("/rules/{rule_id}", response_model=MappingRuleRead)
async def update_rule(
    rule_id: UUID,
    data: MappingRuleUpdate,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> MappingRuleRead:
    rule = await _service.update_rule(session, ctx.workspace_id, rule_id, data)
    await session.commit()
    return MappingRuleRead.model_validate(rule)


# --- Signal endpoints ---


@router.get("/signals/by-node/{node_id}", response_model=list[MappedSignalRead])
async def get_signals_for_node(
    node_id: UUID,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> list[MappedSignalRead]:
    signals = await _service.get_signals_for_node(session, ctx.workspace_id, node_id)
    return [MappedSignalRead.model_validate(s) for s in signals]
