"""Complex SQL queries for the Journey Engine — recursive CTEs, cycle detection."""

from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_ancestor_chain(
    session: AsyncSession, workspace_id: uuid.UUID, node_id: uuid.UUID
) -> list[dict]:
    """Return the chain from root down to the given node using a recursive CTE.

    Returns list of dicts ordered from root (depth=highest) to the target node (depth=0).
    """
    query = text("""
        WITH RECURSIVE ancestors AS (
            SELECT id, parent_node_id, name, type, 0 AS depth
            FROM journey.nodes
            WHERE id = :node_id AND workspace_id = :workspace_id

            UNION ALL

            SELECT n.id, n.parent_node_id, n.name, n.type, a.depth + 1
            FROM journey.nodes n
            JOIN ancestors a ON n.id = a.parent_node_id
        )
        SELECT id, parent_node_id, name, type, depth
        FROM ancestors
        ORDER BY depth DESC
    """)
    result = await session.execute(
        query, {"node_id": node_id, "workspace_id": workspace_id}
    )
    return [dict(row._mapping) for row in result]


async def get_all_descendants(
    session: AsyncSession, workspace_id: uuid.UUID, node_id: uuid.UUID
) -> list[dict]:
    """Return all nodes below the given node in the hierarchy (recursive CTE)."""
    query = text("""
        WITH RECURSIVE descendants AS (
            SELECT id, parent_node_id, name, type, 0 AS depth
            FROM journey.nodes
            WHERE parent_node_id = :node_id AND workspace_id = :workspace_id

            UNION ALL

            SELECT n.id, n.parent_node_id, n.name, n.type, d.depth + 1
            FROM journey.nodes n
            JOIN descendants d ON n.parent_node_id = d.id
        )
        SELECT id, parent_node_id, name, type, depth
        FROM descendants
        ORDER BY depth ASC
    """)
    result = await session.execute(
        query, {"node_id": node_id, "workspace_id": workspace_id}
    )
    return [dict(row._mapping) for row in result]


async def detect_cycle_in_edges(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    source_id: uuid.UUID,
    target_id: uuid.UUID,
) -> bool:
    """DFS-based cycle detection: returns True if adding source→target creates a cycle.

    Starting from target, follow outgoing edges. If we reach source, there's a cycle.
    """
    query = text("""
        WITH RECURSIVE reachable AS (
            SELECT target_node_id AS node_id
            FROM journey.edges
            WHERE source_node_id = :target_id AND workspace_id = :workspace_id

            UNION

            SELECT e.target_node_id
            FROM journey.edges e
            JOIN reachable r ON e.source_node_id = r.node_id
            WHERE e.workspace_id = :workspace_id
        )
        SELECT EXISTS (
            SELECT 1 FROM reachable WHERE node_id = :source_id
        ) AS has_cycle
    """)
    result = await session.execute(
        query,
        {
            "source_id": source_id,
            "target_id": target_id,
            "workspace_id": workspace_id,
        },
    )
    return result.scalar()


async def detect_cycle_in_parents(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    node_id: uuid.UUID,
    proposed_parent_id: uuid.UUID,
) -> bool:
    """Check if setting proposed_parent_id as parent of node_id creates a hierarchy cycle.

    Walk up from proposed_parent_id. If we reach node_id, it's a cycle.
    """
    if node_id == proposed_parent_id:
        return True

    query = text("""
        WITH RECURSIVE ancestors AS (
            SELECT parent_node_id
            FROM journey.nodes
            WHERE id = :proposed_parent_id AND workspace_id = :workspace_id

            UNION ALL

            SELECT n.parent_node_id
            FROM journey.nodes n
            JOIN ancestors a ON n.id = a.parent_node_id
            WHERE n.parent_node_id IS NOT NULL
        )
        SELECT EXISTS (
            SELECT 1 FROM ancestors WHERE parent_node_id = :node_id
        ) AS has_cycle
    """)
    result = await session.execute(
        query,
        {
            "node_id": node_id,
            "proposed_parent_id": proposed_parent_id,
            "workspace_id": workspace_id,
        },
    )
    return result.scalar()
