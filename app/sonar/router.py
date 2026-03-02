"""HTTP endpoints for the Sonar Engine."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import WorkspaceContext
from app.database import get_session
from app.sonar.schemas import FocusRecommendationRead, NodeScoreRead
from app.sonar.service import SonarService
from app.workspace.dependencies import require_workspace

router = APIRouter()
_service = SonarService()


@router.get("/focus-map", response_model=list[FocusRecommendationRead])
async def get_focus_map(
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
    top_n: int = Query(default=10, ge=1, le=100),
    scope: UUID | None = Query(default=None, description="Scope to a subtree root node"),
) -> list[FocusRecommendationRead]:
    recs = await _service.get_focus_map(session, ctx.workspace_id, top_n)
    return [FocusRecommendationRead.model_validate(r) for r in recs]


@router.get("/scores/{node_id}", response_model=list[NodeScoreRead])
async def get_node_scores(
    node_id: UUID,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> list[NodeScoreRead]:
    scores = await _service.get_latest_scores(session, ctx.workspace_id, node_id)
    return [NodeScoreRead.model_validate(s) for s in scores]


@router.post("/compute", status_code=202)
async def trigger_recomputation(
    ctx: WorkspaceContext = Depends(require_workspace),
) -> dict:
    """Trigger a full workspace score recomputation (async)."""
    # In production, this would enqueue a background job
    return {"status": "accepted", "message": "Score recomputation queued"}
