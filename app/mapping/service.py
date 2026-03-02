"""Mapping Engine service — rule evaluation, signal creation, event handling."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.common.types import SignalType
from app.events import event_bus
from app.mapping.engine import evaluate_rule
from app.mapping.models import MappedSignal, MappingRule
from app.mapping.schemas import MappingRuleCreate, MappingRuleUpdate

# Signal type multipliers for computing signal_value
_TYPE_MULTIPLIER = {
    SignalType.POSITIVE: 1.0,
    SignalType.NEGATIVE: -1.0,
    SignalType.NEUTRAL: 0.0,
}


class MappingService:
    # --- Rule CRUD ---

    async def create_rule(
        self, session: AsyncSession, workspace_id: uuid.UUID, data: MappingRuleCreate
    ) -> MappingRule:
        rule = MappingRule(
            workspace_id=workspace_id,
            name=data.name,
            description=data.description,
            target_node_id=data.target_node_id,
            priority=data.priority,
            conditions=data.conditions,
            signal_type=data.signal_type,
            signal_weight=data.signal_weight,
        )
        session.add(rule)
        await session.flush()
        return rule

    async def get_rule(
        self, session: AsyncSession, workspace_id: uuid.UUID, rule_id: uuid.UUID
    ) -> MappingRule:
        rule = await session.get(MappingRule, rule_id)
        if not rule or rule.workspace_id != workspace_id:
            raise NotFoundError("MappingRule", rule_id)
        return rule

    async def list_rules(
        self, session: AsyncSession, workspace_id: uuid.UUID,
        node_id: uuid.UUID | None = None
    ) -> list[MappingRule]:
        stmt = select(MappingRule).where(
            MappingRule.workspace_id == workspace_id,
            MappingRule.is_active.is_(True),
        )
        if node_id:
            stmt = stmt.where(MappingRule.target_node_id == node_id)
        stmt = stmt.order_by(MappingRule.priority.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_rule(
        self, session: AsyncSession, workspace_id: uuid.UUID,
        rule_id: uuid.UUID, data: MappingRuleUpdate
    ) -> MappingRule:
        rule = await self.get_rule(session, workspace_id, rule_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)
        await session.flush()
        return rule

    # --- Core Mapping Logic ---

    async def map_event(
        self, session: AsyncSession, workspace_id: uuid.UUID, event_data: dict
    ) -> list[MappedSignal]:
        """Evaluate all active rules against an event. Create MappedSignals for matches."""
        rules = await self.list_rules(session, workspace_id)

        signals: list[MappedSignal] = []
        for rule in rules:
            if evaluate_rule(rule.conditions, event_data):
                signal_value = rule.signal_weight * _TYPE_MULTIPLIER[rule.signal_type]
                signal = MappedSignal(
                    workspace_id=workspace_id,
                    normalized_event_id=uuid.UUID(event_data["normalized_event_id"]),
                    mapping_rule_id=rule.id,
                    node_id=rule.target_node_id,
                    actor_id=event_data.get("actor_id"),
                    signal_type=rule.signal_type,
                    signal_weight=rule.signal_weight,
                    signal_value=signal_value,
                    event_occurred_at=event_data["occurred_at"],
                )
                session.add(signal)
                signals.append(signal)

        if signals:
            await session.flush()
            for signal in signals:
                await event_bus.publish("mapping.signal.created", {
                    "workspace_id": str(workspace_id),
                    "signal_id": str(signal.id),
                    "node_id": str(signal.node_id),
                    "signal_type": signal.signal_type.value,
                    "signal_value": signal.signal_value,
                    "actor_id": signal.actor_id,
                    "occurred_at": str(signal.event_occurred_at),
                })

        return signals

    # --- Event Bus Handler ---

    async def handle_normalized_event(self, payload: dict[str, Any]) -> None:
        """Called by the event bus when ingestion.event.normalized fires.

        Note: In a real implementation, this would acquire its own DB session.
        For now, this is a stub that demonstrates the wiring.
        """
        # TODO: Acquire a session from the session factory and call self.map_event()
        pass

    # --- Signal Queries (for Sonar) ---

    async def get_signals_for_node(
        self, session: AsyncSession, workspace_id: uuid.UUID, node_id: uuid.UUID
    ) -> list[MappedSignal]:
        result = await session.execute(
            select(MappedSignal).where(
                MappedSignal.workspace_id == workspace_id,
                MappedSignal.node_id == node_id,
            ).order_by(MappedSignal.event_occurred_at.desc())
        )
        return list(result.scalars().all())
