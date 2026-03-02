"""Sonar Engine service — scoring, focus map generation, event handling."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.types import ScoreType
from app.sonar.models import FocusRecommendation, NodeScore
from app.sonar.schemas import FocusRecommendationRead, NodeScoreRead
from app.sonar.scoring import (
    compute_composite_score,
    compute_health_score,
    compute_opportunity_score,
    compute_urgency_score,
)


class SonarService:
    # --- Score Storage ---

    async def store_node_score(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        node_id: uuid.UUID,
        score_type: ScoreType,
        value: float,
        components: dict,
        time_window: str = "P7D",
    ) -> NodeScore:
        score = NodeScore(
            workspace_id=workspace_id,
            node_id=node_id,
            score_type=score_type,
            value=value,
            components=components,
            time_window=time_window,
        )
        session.add(score)
        await session.flush()
        return score

    async def get_latest_scores(
        self, session: AsyncSession, workspace_id: uuid.UUID, node_id: uuid.UUID
    ) -> list[NodeScore]:
        """Get the most recent score of each type for a node."""
        scores = []
        for st in ScoreType:
            result = await session.execute(
                select(NodeScore)
                .where(
                    NodeScore.workspace_id == workspace_id,
                    NodeScore.node_id == node_id,
                    NodeScore.score_type == st,
                )
                .order_by(NodeScore.computed_at.desc())
                .limit(1)
            )
            score = result.scalar_one_or_none()
            if score:
                scores.append(score)
        return scores

    # --- Score Computation ---

    async def compute_node_scores(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        node_id: uuid.UUID,
        signal_counts: dict,
        goal_gaps: list[dict],
        current_negative_rate: float = 0.0,
        previous_negative_rate: float = 0.0,
        descendant_count: int = 0,
        time_window: str = "P7D",
    ) -> list[NodeScore]:
        """Compute all four score types for a node and store them."""
        scores = []

        # Health
        health_val, health_comp = compute_health_score(
            signal_counts.get("positive", 0),
            signal_counts.get("negative", 0),
            signal_counts.get("neutral", 0),
        )
        scores.append(await self.store_node_score(
            session, workspace_id, node_id,
            ScoreType.HEALTH, health_val, health_comp, time_window,
        ))

        # Opportunity
        opp_val, opp_comp = compute_opportunity_score(goal_gaps)
        scores.append(await self.store_node_score(
            session, workspace_id, node_id,
            ScoreType.OPPORTUNITY, opp_val, opp_comp, time_window,
        ))

        # Urgency
        urg_val, urg_comp = compute_urgency_score(
            goal_gaps, current_negative_rate, previous_negative_rate, descendant_count,
        )
        scores.append(await self.store_node_score(
            session, workspace_id, node_id,
            ScoreType.URGENCY, urg_val, urg_comp, time_window,
        ))

        # Composite
        comp_val, comp_comp = compute_composite_score(health_val, opp_val, urg_val)
        scores.append(await self.store_node_score(
            session, workspace_id, node_id,
            ScoreType.COMPOSITE, comp_val, comp_comp, time_window,
        ))

        return scores

    # --- Focus Map ---

    async def get_focus_map(
        self, session: AsyncSession, workspace_id: uuid.UUID, top_n: int = 10
    ) -> list[FocusRecommendation]:
        """Get the ranked focus recommendations (highest composite score first)."""
        result = await session.execute(
            select(FocusRecommendation)
            .where(FocusRecommendation.workspace_id == workspace_id)
            .order_by(FocusRecommendation.rank.asc())
            .limit(top_n)
        )
        return list(result.scalars().all())

    # --- Event Bus Handler ---

    async def handle_new_signal(self, payload: dict[str, Any]) -> None:
        """Called by the event bus when mapping.signal.created fires.

        Marks affected node scores as stale and schedules recomputation.
        In a full implementation, this would:
        1. Look up the node_id from the payload
        2. Mark that node's scores as stale
        3. Schedule a recomputation (debounced to avoid recomputing on every single event)
        """
        # TODO: Implement stale-marking and debounced recomputation
        pass
