import { useCallback, useEffect, useState } from "react";
import type { NodeRead, NodeTree } from "../types";
import { createEdge, createNode, deleteEdge, deleteNode, getTree, listRoots, updateEdge, updateNode, uploadJourney } from "../api/journeys";

function findNodeInTree(tree: NodeTree, nodeId: string): NodeRead | null {
  if (tree.node.id === nodeId) return tree.node;
  for (const child of tree.children) {
    const found = findNodeInTree(child, nodeId);
    if (found) return found;
  }
  return null;
}

function patchNodeMetaInTree(tree: NodeTree, nodeId: string, meta: Record<string, unknown>): NodeTree {
  if (tree.node.id === nodeId) {
    return { ...tree, node: { ...tree.node, metadata: meta } };
  }
  return { ...tree, children: tree.children.map((c) => patchNodeMetaInTree(c, nodeId, meta)) };
}

export function useJourney() {
  const [roots, setRoots] = useState<NodeRead[]>([]);
  const [tree, setTree] = useState<NodeTree | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRoots = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await listRoots();
      setRoots(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load journeys");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRoots();
  }, [fetchRoots]);

  const selectRoot = useCallback(async (rootId: string) => {
    setLoading(true);
    setError(null);
    try {
      const t = await getTree(rootId);
      setTree(t);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load tree");
    } finally {
      setLoading(false);
    }
  }, []);

  const upload = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const t = await uploadJourney(file);
      setTree(t);
      const r = await listRoots();
      setRoots(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }, []);

  const saveNode = useCallback(
    async (nodeId: string, data: { name?: string; metadata?: Record<string, unknown> }) => {
      setError(null);
      try {
        // Preserve canvas position (_x/_y) when saving content metadata
        let metadata = data.metadata;
        if (metadata && tree) {
          const existing = findNodeInTree(tree, nodeId)?.metadata as Record<string, unknown> | undefined;
          if (existing?._x !== undefined || existing?._y !== undefined) {
            metadata = { ...metadata };
            if (existing._x !== undefined) metadata._x = existing._x;
            if (existing._y !== undefined) metadata._y = existing._y;
          }
        }
        await updateNode(nodeId, { ...data, metadata });
        if (tree) {
          const t = await getTree(tree.node.id);
          setTree(t);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Save failed");
        throw e;
      }
    },
    [tree],
  );

  const moveNode = useCallback(
    async (nodeId: string, x: number, y: number, currentMetadata: Record<string, unknown>) => {
      const newMeta = { ...currentMetadata, _x: x, _y: y };
      // Update tree in memory immediately so useEffect re-layout uses new position
      setTree((prev) => (prev ? patchNodeMetaInTree(prev, nodeId, newMeta) : prev));
      try {
        await updateNode(nodeId, { metadata: newMeta });
      } catch {
        // position save failure is non-critical
      }
    },
    [],
  );

  // Insert a new stage at `atIndex` (0 = before first, length = after last).
  // Bumps positions of all existing stages at >= atIndex first.
  const addStage = useCallback(
    async (name: string, atIndex?: number) => {
      if (!tree) return;
      setError(null);
      const insertAt = atIndex ?? tree.children.length;
      try {
        // Bump existing stages that are at or after the insert point
        await Promise.all(
          tree.children
            .filter((s) => s.node.position >= insertAt)
            .map((s) => updateNode(s.node.id, { position: s.node.position + 1 })),
        );
        await createNode({
          name,
          type: "STAGE",
          parent_node_id: tree.node.id,
          position: insertAt,
        });
        const t = await getTree(tree.node.id);
        setTree(t);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to add stage");
      }
    },
    [tree],
  );

  const deleteStage = useCallback(
    async (stageId: string) => {
      if (!tree) return;
      setError(null);
      try {
        await deleteNode(stageId);
        const t = await getTree(tree.node.id);
        setTree(t);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to delete stage");
      }
    },
    [tree],
  );

  const addTouchpoint = useCallback(
    async (stageId: string, name: string, atIndex?: number) => {
      if (!tree) return;
      setError(null);
      try {
        const stage = tree.children.find((c) => c.node.id === stageId);
        const insertAt = atIndex ?? (stage?.children.length ?? 0);
        // Bump existing touchpoints at or after insert point
        await Promise.all(
          (stage?.children ?? [])
            .filter((tp) => tp.node.position >= insertAt)
            .map((tp) => updateNode(tp.node.id, { position: tp.node.position + 1 })),
        );
        await createNode({
          name,
          type: "TOUCHPOINT",
          parent_node_id: stageId,
          position: insertAt,
          metadata: {
            businessRule: "",
            feature: "",
            dataPoints: [],
            edgeCases: [],
            emails: [],
          },
        });
        const t = await getTree(tree.node.id);
        setTree(t);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to add touchpoint");
      }
    },
    [tree],
  );

  const deleteTouchpoint = useCallback(
    async (tpId: string) => {
      if (!tree) return;
      setError(null);
      try {
        await deleteNode(tpId);
        const t = await getTree(tree.node.id);
        setTree(t);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to delete touchpoint");
      }
    },
    [tree],
  );

  const addEdge = useCallback(
    async (sourceId: string, targetId: string) => {
      if (!tree) return;
      setError(null);
      try {
        await createEdge({ source_node_id: sourceId, target_node_id: targetId, metadata: { label: "" } });
        const t = await getTree(tree.node.id);
        setTree(t);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to create connection");
      }
    },
    [tree],
  );

  const saveEdgeLabel = useCallback(
    async (edgeId: string, label: string) => {
      if (!tree) return;
      setError(null);
      try {
        await updateEdge(edgeId, { metadata: { label } });
        const t = await getTree(tree.node.id);
        setTree(t);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to update connection");
      }
    },
    [tree],
  );

  const removeEdge = useCallback(
    async (edgeId: string) => {
      if (!tree) return;
      setError(null);
      try {
        await deleteEdge(edgeId);
        const t = await getTree(tree.node.id);
        setTree(t);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to delete connection");
      }
    },
    [tree],
  );

  const clearTree = useCallback(() => setTree(null), []);

  return {
    roots, tree, loading, error,
    selectRoot, upload, saveNode, moveNode,
    addStage, deleteStage,
    addTouchpoint, deleteTouchpoint,
    addEdge, saveEdgeLabel, removeEdge,
    clearTree,
  };
}
