"""Tree manipulation utilities for building nested node structures."""

from __future__ import annotations

from uuid import UUID

from app.journey.schemas import EdgeRead, NodeRead, NodeTree


def build_tree(
    nodes: list[NodeRead], edges: list[EdgeRead], root_id: UUID
) -> NodeTree:
    """Build a nested NodeTree from flat lists of nodes and edges."""
    node_map: dict[UUID, NodeRead] = {n.id: n for n in nodes}
    children_map: dict[UUID, list[NodeRead]] = {}
    edge_map: dict[UUID, list[EdgeRead]] = {}

    for node in nodes:
        parent = node.parent_node_id
        if parent is not None:
            children_map.setdefault(parent, []).append(node)

    for edge in edges:
        edge_map.setdefault(edge.source_node_id, []).append(edge)

    def _build(node_id: UUID) -> NodeTree:
        node = node_map[node_id]
        child_nodes = children_map.get(node_id, [])
        child_nodes.sort(key=lambda n: n.position)
        return NodeTree(
            node=node,
            children=[_build(c.id) for c in child_nodes],
            edges=edge_map.get(node_id, []),
        )

    return _build(root_id)
