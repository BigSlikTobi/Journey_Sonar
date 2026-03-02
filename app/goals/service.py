"""Goal Engine service — goal CRUD, snapshot computation."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.common.types import GoalStatus
from app.goals.metrics import compute_metric, determine_goal_status
from app.goals.models import Goal, GoalSnapshot
from app.goals.schemas import GoalCreate, GoalUpdate, GoalsSummary


class GoalService:
    # --- Goal CRUD ---

    async def create_goal(
        self, session: AsyncSession, workspace_id: uuid.UUID, data: GoalCreate
    ) -> Goal:
        goal = Goal(
            workspace_id=workspace_id,
            name=data.name,
            description=data.description,
            goal_type=data.goal_type,
            target_node_id=data.target_node_id,
            metric_definition=data.metric_definition,
            target_value=data.target_value,
            target_direction=data.target_direction,
            target_range=data.target_range,
            time_window=data.time_window,
            priority=data.priority,
        )
        session.add(goal)
        await session.flush()
        return goal

    async def get_goal(
        self, session: AsyncSession, workspace_id: uuid.UUID, goal_id: uuid.UUID
    ) -> Goal:
        goal = await session.get(Goal, goal_id)
        if not goal or goal.workspace_id != workspace_id:
            raise NotFoundError("Goal", goal_id)
        return goal

    async def list_goals(
        self, session: AsyncSession, workspace_id: uuid.UUID,
        node_id: uuid.UUID | None = None
    ) -> list[Goal]:
        stmt = select(Goal).where(
            Goal.workspace_id == workspace_id, Goal.is_active.is_(True)
        )
        if node_id:
            stmt = stmt.where(Goal.target_node_id == node_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_goal(
        self, session: AsyncSession, workspace_id: uuid.UUID,
        goal_id: uuid.UUID, data: GoalUpdate
    ) -> Goal:
        goal = await self.get_goal(session, workspace_id, goal_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(goal, field, value)
        await session.flush()
        return goal

    # --- Snapshot Computation ---

    async def compute_snapshot(
        self, session: AsyncSession, workspace_id: uuid.UUID, goal_id: uuid.UUID,
        signal_data: dict | None = None,
    ) -> GoalSnapshot:
        """Compute a goal snapshot from current signal data.

        In a full implementation, signal_data would be fetched from MappingService.
        For now, accepts it as a parameter for flexibility.
        """
        goal = await self.get_goal(session, workspace_id, goal_id)

        if signal_data is None:
            signal_data = {}

        current_value = compute_metric(
            goal.goal_type, goal.metric_definition, signal_data
        )
        status = determine_goal_status(
            current_value, goal.target_value, goal.target_direction, goal.target_range
        )
        gap = goal.target_value - current_value
        gap_pct = (gap / goal.target_value * 100) if goal.target_value != 0 else 0.0

        snapshot = GoalSnapshot(
            workspace_id=workspace_id,
            goal_id=goal_id,
            current_value=current_value,
            target_value=goal.target_value,
            gap=gap,
            gap_percentage=gap_pct,
            status=status,
            computation_details={
                "signal_data": signal_data,
                "metric_type": goal.goal_type.value,
            },
        )
        session.add(snapshot)
        await session.flush()
        return snapshot

    async def get_latest_snapshot(
        self, session: AsyncSession, workspace_id: uuid.UUID, goal_id: uuid.UUID
    ) -> GoalSnapshot | None:
        result = await session.execute(
            select(GoalSnapshot)
            .where(GoalSnapshot.goal_id == goal_id, GoalSnapshot.workspace_id == workspace_id)
            .order_by(GoalSnapshot.snapshot_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_goal_history(
        self, session: AsyncSession, workspace_id: uuid.UUID, goal_id: uuid.UUID
    ) -> list[GoalSnapshot]:
        result = await session.execute(
            select(GoalSnapshot)
            .where(GoalSnapshot.goal_id == goal_id, GoalSnapshot.workspace_id == workspace_id)
            .order_by(GoalSnapshot.snapshot_at.desc())
        )
        return list(result.scalars().all())

    async def get_goals_summary(
        self, session: AsyncSession, workspace_id: uuid.UUID
    ) -> GoalsSummary:
        """Get aggregate counts of goals by their latest snapshot status."""
        goals = await self.list_goals(session, workspace_id)
        summary = GoalsSummary(total=len(goals))

        for goal in goals:
            snapshot = await self.get_latest_snapshot(session, workspace_id, goal.id)
            if not snapshot:
                continue
            match snapshot.status:
                case GoalStatus.ON_TRACK:
                    summary.on_track += 1
                case GoalStatus.AT_RISK:
                    summary.at_risk += 1
                case GoalStatus.OFF_TRACK:
                    summary.off_track += 1
                case GoalStatus.EXCEEDED:
                    summary.exceeded += 1

        return summary
