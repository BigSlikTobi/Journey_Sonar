"""Import a journey JSON structure into the node hierarchy."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.types import NodeType
from app.journey.import_schemas import JourneyImport
from app.journey.models import Node


class JourneyImporter:
    async def import_journey(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        data: JourneyImport,
    ) -> Node:
        """Create a full JOURNEY_ROOT → STAGE → TOUCHPOINT tree from import data."""
        root = Node(
            workspace_id=workspace_id,
            name=data.journeyName,
            type=NodeType.JOURNEY_ROOT,
            metadata_={"version": data.version},
            position=0,
        )
        session.add(root)
        await session.flush()

        for stage_idx, stage in enumerate(data.stages):
            stage_node = Node(
                workspace_id=workspace_id,
                name=stage.title,
                type=NodeType.STAGE,
                parent_node_id=root.id,
                position=stage_idx,
            )
            session.add(stage_node)
            await session.flush()

            for tp_idx, tp in enumerate(stage.items):
                tp_node = Node(
                    workspace_id=workspace_id,
                    name=tp.touchpoint,
                    type=NodeType.TOUCHPOINT,
                    parent_node_id=stage_node.id,
                    position=tp_idx,
                    metadata_={
                        "businessRule": tp.businessRule,
                        "feature": tp.feature,
                        "dataPoints": tp.dataPoints,
                        "edgeCases": tp.edgeCases,
                        "emails": [e.model_dump() for e in tp.emails],
                    },
                )
                session.add(tp_node)

        await session.flush()
        return root
