"""HTTP endpoints for the Goal Engine."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import WorkspaceContext
from app.database import get_session
from app.goals.schemas import (
    GoalCreate,
    GoalRead,
    GoalSnapshotRead,
    GoalsSummary,
    GoalUpdate,
)
from app.goals.service import GoalService
from app.workspace.dependencies import require_workspace

router = APIRouter()
_service = GoalService()


@router.post("", response_model=GoalRead, status_code=201)
async def create_goal(
    data: GoalCreate,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> GoalRead:
    goal = await _service.create_goal(session, ctx.workspace_id, data)
    await session.commit()
    return GoalRead.model_validate(goal)


@router.get("", response_model=list[GoalRead])
async def list_goals(
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
    node_id: UUID | None = Query(default=None),
) -> list[GoalRead]:
    goals = await _service.list_goals(session, ctx.workspace_id, node_id)
    return [GoalRead.model_validate(g) for g in goals]


@router.get("/summary", response_model=GoalsSummary)
async def get_summary(
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> GoalsSummary:
    return await _service.get_goals_summary(session, ctx.workspace_id)


@router.get("/{goal_id}", response_model=GoalRead)
async def get_goal(
    goal_id: UUID,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> GoalRead:
    goal = await _service.get_goal(session, ctx.workspace_id, goal_id)
    return GoalRead.model_validate(goal)


@router.patch("/{goal_id}", response_model=GoalRead)
async def update_goal(
    goal_id: UUID,
    data: GoalUpdate,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> GoalRead:
    goal = await _service.update_goal(session, ctx.workspace_id, goal_id, data)
    await session.commit()
    return GoalRead.model_validate(goal)


@router.get("/{goal_id}/history", response_model=list[GoalSnapshotRead])
async def get_goal_history(
    goal_id: UUID,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> list[GoalSnapshotRead]:
    snapshots = await _service.get_goal_history(session, ctx.workspace_id, goal_id)
    return [GoalSnapshotRead.model_validate(s) for s in snapshots]


@router.post("/{goal_id}/compute", response_model=GoalSnapshotRead)
async def compute_snapshot(
    goal_id: UUID,
    ctx: WorkspaceContext = Depends(require_workspace),
    session: AsyncSession = Depends(get_session),
) -> GoalSnapshotRead:
    snapshot = await _service.compute_snapshot(session, ctx.workspace_id, goal_id)
    await session.commit()
    return GoalSnapshotRead.model_validate(snapshot)
