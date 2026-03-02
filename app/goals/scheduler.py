"""Periodic goal snapshot computation.

In production, this would be triggered by a task scheduler (e.g., APScheduler, Celery Beat).
This module provides the computation function that the scheduler calls.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.goals.models import Goal
from app.goals.service import GoalService

logger = logging.getLogger(__name__)


async def compute_all_snapshots(session: AsyncSession, workspace_id: uuid.UUID) -> int:
    """Compute snapshots for all active goals in a workspace.

    Returns the number of snapshots created.
    """
    goal_service = GoalService()
    result = await session.execute(
        select(Goal).where(
            Goal.workspace_id == workspace_id,
            Goal.is_active.is_(True),
        )
    )
    goals = result.scalars().all()

    count = 0
    for goal in goals:
        try:
            await goal_service.compute_snapshot(session, workspace_id, goal.id)
            count += 1
        except Exception:
            logger.exception("Failed to compute snapshot for goal %s", goal.id)

    return count
