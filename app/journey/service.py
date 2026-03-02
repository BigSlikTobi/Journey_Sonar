"""Journey Engine service — business logic for nodes, edges, and graph operations."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import CycleDetectedError, NotFoundError, ValidationError
from app.common.types import NodeType
from app.journey.models import Edge, Node
from app.journey.queries import (
    detect_cycle_in_edges,
    detect_cycle_in_parents,
    get_all_descendants,
    get_ancestor_chain,
)
from app.journey.schemas import EdgeCreate, NodeCreate, NodeMatch, NodeUpdate


class JourneyService:
    # --- Node CRUD ---

    async def create_node(
        self, session: AsyncSession, workspace_id: uuid.UUID, data: NodeCreate
    ) -> Node:
        if data.parent_node_id:
            parent = await session.get(Node, data.parent_node_id)
            if not parent or parent.workspace_id != workspace_id:
                raise NotFoundError("Parent Node", data.parent_node_id)

        node = Node(
            workspace_id=workspace_id,
            name=data.name,
            type=data.type,
            parent_node_id=data.parent_node_id,
            input_schema=data.input_schema,
            output_schema=data.output_schema,
            metadata_=data.metadata,
            position=data.position,
        )
        session.add(node)
        await session.flush()
        return node

    async def get_node(
        self, session: AsyncSession, workspace_id: uuid.UUID, node_id: uuid.UUID
    ) -> Node:
        node = await session.get(Node, node_id)
        if not node or node.workspace_id != workspace_id:
            raise NotFoundError("Node", node_id)
        return node

    async def update_node(
        self, session: AsyncSession, workspace_id: uuid.UUID, node_id: uuid.UUID, data: NodeUpdate
    ) -> Node:
        node = await self.get_node(session, workspace_id, node_id)

        if data.parent_node_id is not None and data.parent_node_id != node.parent_node_id:
            has_cycle = await detect_cycle_in_parents(
                session, workspace_id, node_id, data.parent_node_id
            )
            if has_cycle:
                raise CycleDetectedError(node_id, data.parent_node_id)
            node.parent_node_id = data.parent_node_id

        if data.name is not None:
            node.name = data.name
        if data.type is not None:
            node.type = data.type
        if data.input_schema is not None:
            node.input_schema = data.input_schema
        if data.output_schema is not None:
            node.output_schema = data.output_schema
        if data.metadata is not None:
            node.metadata_ = data.metadata
        if data.position is not None:
            node.position = data.position

        await session.flush()
        return node

    async def delete_node(
        self, session: AsyncSession, workspace_id: uuid.UUID, node_id: uuid.UUID
    ) -> None:
        node = await self.get_node(session, workspace_id, node_id)
        await session.delete(node)
        await session.flush()

    # --- Sub-journey / hierarchy ---

    async def get_sub_journey(
        self, session: AsyncSession, workspace_id: uuid.UUID, node_id: uuid.UUID
    ) -> list[Node]:
        """Get direct children of a node."""
        result = await session.execute(
            select(Node)
            .where(Node.workspace_id == workspace_id, Node.parent_node_id == node_id)
            .order_by(Node.position)
        )
        return list(result.scalars().all())

    async def get_ancestor_chain(
        self, session: AsyncSession, workspace_id: uuid.UUID, node_id: uuid.UUID
    ) -> list[dict]:
        return await get_ancestor_chain(session, workspace_id, node_id)

    async def get_all_descendants(
        self, session: AsyncSession, workspace_id: uuid.UUID, node_id: uuid.UUID
    ) -> list[dict]:
        return await get_all_descendants(session, workspace_id, node_id)

    # --- Edge CRUD ---

    async def create_edge(
        self, session: AsyncSession, workspace_id: uuid.UUID, data: EdgeCreate
    ) -> Edge:
        # Validate both nodes exist in this workspace
        await self.get_node(session, workspace_id, data.source_node_id)
        await self.get_node(session, workspace_id, data.target_node_id)

        if data.source_node_id == data.target_node_id:
            raise ValidationError("Cannot create self-referencing edge")

        has_cycle = await detect_cycle_in_edges(
            session, workspace_id, data.source_node_id, data.target_node_id
        )
        if has_cycle:
            raise CycleDetectedError(data.source_node_id, data.target_node_id)

        edge = Edge(
            workspace_id=workspace_id,
            source_node_id=data.source_node_id,
            target_node_id=data.target_node_id,
            condition=data.condition,
            is_fallback=data.is_fallback,
            weight=data.weight,
            metadata_=data.metadata,
        )
        session.add(edge)
        await session.flush()
        return edge

    async def get_outgoing_edges(
        self, session: AsyncSession, workspace_id: uuid.UUID, node_id: uuid.UUID
    ) -> list[Edge]:
        result = await session.execute(
            select(Edge).where(
                Edge.workspace_id == workspace_id, Edge.source_node_id == node_id
            )
        )
        return list(result.scalars().all())

    async def delete_edge(
        self, session: AsyncSession, workspace_id: uuid.UUID, edge_id: uuid.UUID
    ) -> None:
        edge = await session.get(Edge, edge_id)
        if not edge or edge.workspace_id != workspace_id:
            raise NotFoundError("Edge", edge_id)
        await session.delete(edge)
        await session.flush()

    # --- Input schema matching (used by Mapping Engine) ---

    async def match_node_by_input(
        self, session: AsyncSession, workspace_id: uuid.UUID, data_payload: dict
    ) -> list[NodeMatch]:
        """Match an incoming data payload against input_schemas of leaf nodes.

        Evaluates TOUCHPOINT and MICRO_ACTION nodes. Returns ranked matches.
        """
        result = await session.execute(
            select(Node).where(
                Node.workspace_id == workspace_id,
                Node.type.in_([NodeType.TOUCHPOINT, NodeType.MICRO_ACTION]),
            )
        )
        nodes = result.scalars().all()

        matches: list[NodeMatch] = []
        for node in nodes:
            if not node.input_schema:
                continue
            matched_fields = [
                key for key in node.input_schema
                if key in data_payload and data_payload[key] == node.input_schema[key]
            ]
            if not matched_fields:
                continue
            confidence = len(matched_fields) / len(node.input_schema)
            matches.append(
                NodeMatch(
                    node_id=node.id,
                    node_name=node.name,
                    confidence=confidence,
                    matched_fields=matched_fields,
                )
            )

        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches
