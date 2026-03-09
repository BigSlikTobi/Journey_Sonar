import React from "react";
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  applyNodeChanges,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge as RFEdge,
  type Node as RFNode,
  type NodeChange,
  type NodeProps,
  type EdgeProps,
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useRef, useState } from "react";
import type { EdgeRead, NodeRead, NodeTree, TouchpointMetadata } from "../types";

type Highlight = "feature" | "businessRule" | "dataPoints" | "emails";
const HIGHLIGHT_OPTIONS: { value: Highlight; label: string }[] = [
  { value: "feature", label: "Feature" },
  { value: "businessRule", label: "Business Rule" },
  { value: "dataPoints", label: "Data Points" },
  { value: "emails", label: "Emails" },
];
import { TouchpointEditor } from "./TouchpointEditor";

// ─── helpers ─────────────────────────────────────────────────────────────────

function flattenTree(tree: NodeTree): { nodes: NodeRead[]; edges: EdgeRead[] } {
  const nodes: NodeRead[] = [tree.node];
  const edges: EdgeRead[] = [...tree.edges];
  for (const child of tree.children) {
    const r = flattenTree(child);
    nodes.push(...r.nodes);
    edges.push(...r.edges);
  }
  return { nodes, edges };
}

const STAGE_W = 240;
const STAGE_H = 52;
const TP_W = 220;
const TP_H = 88;
const COL_GAP = 80;
const TP_Y_START = 24;
const TP_Y_GAP = 12;

// Re-stack touchpoints under their parent stages using actual measured heights.
function restackTouchpoints(nodes: RFNode[], tree: NodeTree): RFNode[] {
  const byId = new Map(nodes.map((n) => [n.id, { ...n }]));

  tree.children.forEach((stage) => {
    const stageNode = byId.get(stage.node.id);
    if (!stageNode) return;
    const sx = stageNode.position.x;
    const sy = stageNode.position.y;
    const stageH = (stageNode.measured?.height as number | undefined) ?? STAGE_H;

    let y = sy + stageH + TP_Y_START;
    stage.children.forEach((tp) => {
      const rfNode = byId.get(tp.node.id);
      if (!rfNode) return;
      rfNode.position = { x: sx + (STAGE_W - TP_W) / 2, y };
      y += ((rfNode.measured?.height as number | undefined) ?? TP_H) + TP_Y_GAP;
    });
  });

  return nodes.map((n) => byId.get(n.id) ?? n);
}

function buildLayout(tree: NodeTree): { rfNodes: RFNode[]; rfEdges: RFEdge[] } {
  const { edges } = flattenTree(tree);
  const rfNodes: RFNode[] = [];
  const rfEdges: RFEdge[] = [];

  const stages = tree.children;
  const colW = STAGE_W + COL_GAP;

  stages.forEach((stage, si) => {
    const sm = stage.node.metadata as Record<string, unknown>;
    const sx = (sm?._x as number) ?? si * colW;
    const sy = (sm?._y as number) ?? 0;
    rfNodes.push({
      id: stage.node.id,
      type: "stage",
      position: { x: sx, y: sy },
      data: { node: stage.node },
      style: { width: STAGE_W },
    });

    stage.children.forEach((tp, ti) => {
      rfNodes.push({
        id: tp.node.id,
        type: "touchpoint",
        position: { x: sx + (STAGE_W - TP_W) / 2, y: sy + STAGE_H + TP_Y_START + ti * (TP_H + TP_Y_GAP) },
        data: { node: tp.node },
        style: { width: TP_W },
      });
    });
  });

  edges.forEach((e) => {
    rfEdges.push({
      id: e.id,
      source: e.source_node_id,
      target: e.target_node_id,
      type: "labeled",
      data: { label: (e.metadata?.label as string) || "", edgeId: e.id },
      animated: false,
    });
  });

  return { rfNodes, rfEdges };
}

// ─── custom node: Stage ───────────────────────────────────────────────────────

function StageNode({ data }: NodeProps) {
  const node = data.node as NodeRead;
  const onDelete = data.onDelete as ((id: string) => Promise<void>) | undefined;
  const onAddTp = data.onAddTouchpoint as ((stageId: string, name: string) => Promise<void>) | undefined;
  const [adding, setAdding] = useState(false);
  const [tpName, setTpName] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <div className="rounded-lg border-2 border-indigo-300 bg-indigo-50 shadow-sm select-none"
         style={{ width: STAGE_W }}>
      <Handle type="target" position={Position.Left} className="!w-3 !h-3 !bg-indigo-400" />
      <Handle type="source" position={Position.Right} className="!w-3 !h-3 !bg-indigo-400" />
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-indigo-400" id="top" />
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-indigo-400" id="bottom" />
      <div className="px-3 py-2 flex items-start justify-between">
        <div>
          <p className="text-xs font-bold text-indigo-700 uppercase tracking-wide">Stage</p>
          <p className="text-sm font-semibold text-gray-800 leading-tight">{node.name}</p>
        </div>
        {confirmDelete ? (
          <div className="flex items-center gap-1 ml-1">
            <button onClick={() => onDelete?.(node.id)} className="rounded px-1.5 py-0.5 text-[10px] bg-red-600 text-white hover:bg-red-700">Yes</button>
            <button onClick={() => setConfirmDelete(false)} className="rounded px-1.5 py-0.5 text-[10px] bg-gray-200 text-gray-600">No</button>
          </div>
        ) : (
          <button onClick={() => setConfirmDelete(true)} className="ml-1 text-gray-300 hover:text-red-500 text-base leading-none" title="Delete stage">×</button>
        )}
      </div>
      {adding ? (
        <div className="px-2 pb-2 space-y-1 nodrag">
          <input
            autoFocus
            value={tpName}
            onChange={(e) => setTpName(e.target.value)}
            onKeyDown={async (e) => {
              if (e.key === "Enter" && tpName.trim()) { await onAddTp?.(node.id, tpName.trim()); setTpName(""); setAdding(false); }
              if (e.key === "Escape") { setAdding(false); setTpName(""); }
            }}
            placeholder="Touchpoint name…"
            className="w-full rounded border border-gray-300 px-2 py-1 text-xs focus:border-blue-400 focus:outline-none"
          />
          <div className="flex gap-1">
            <button onClick={async () => { if (tpName.trim()) { await onAddTp?.(node.id, tpName.trim()); setTpName(""); setAdding(false); } }} className="rounded bg-blue-600 px-2 py-0.5 text-[10px] text-white">Add</button>
            <button onClick={() => { setAdding(false); setTpName(""); }} className="text-[10px] text-gray-400 hover:text-gray-600">Cancel</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setAdding(true)} className="nodrag w-full border-t border-indigo-200 py-1 text-[10px] text-indigo-500 hover:bg-indigo-100 transition-colors">
          + Add Touchpoint
        </button>
      )}
    </div>
  );
}

// ─── custom node: Touchpoint ──────────────────────────────────────────────────

function TouchpointNode({ data }: NodeProps) {
  const node = data.node as NodeRead;
  const onOpen = data.onOpen as ((node: NodeRead) => void) | undefined;
  const onDelete = data.onDelete as ((id: string) => Promise<void>) | undefined;
  const highlight = (data.highlight as Highlight) ?? "feature";
  const meta = node.metadata as unknown as TouchpointMetadata;
  const dpCount = meta?.dataPoints?.length ?? 0;
  const ecCount = meta?.edgeCases?.length ?? 0;
  const emailCount = meta?.emails?.length ?? 0;

  return (
    <div
      className="rounded-lg border border-gray-200 bg-white shadow-sm cursor-pointer hover:border-blue-400 hover:shadow transition-all select-none"
      style={{ width: TP_W }}
      onDoubleClick={() => onOpen?.(node)}
    >
      <Handle type="target" position={Position.Left} className="!w-3 !h-3 !bg-blue-400" />
      <Handle type="source" position={Position.Right} className="!w-3 !h-3 !bg-blue-400" />
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-blue-400" id="top" />
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-blue-400" id="bottom" />
      <div className="px-3 py-2">
        <div className="flex items-start justify-between mb-1">
          <p className="text-sm font-semibold text-gray-800 leading-tight pr-2">{node.name}</p>
          <button onClick={(e) => { e.stopPropagation(); onDelete?.(node.id); }} className="nodrag flex-shrink-0 text-gray-300 hover:text-red-500 text-base leading-none" title="Delete touchpoint">×</button>
        </div>

        {/* Highlight preview */}
        {highlight === "feature" && meta?.feature && (
          <p className="text-[11px] text-gray-400 mb-1.5 whitespace-pre-wrap">{meta.feature}</p>
        )}
        {highlight === "businessRule" && (
          <>
            {meta?.businessRule && (
              <p className="text-[11px] text-gray-400 mb-1.5 whitespace-pre-wrap">{meta.businessRule}</p>
            )}
            {ecCount > 0 && (
              <ul className="mb-1.5 space-y-0.5">
                {meta.edgeCases.map((ec, i) => (
                  <li key={i} className="text-[11px] text-amber-600">· {ec}</li>
                ))}
              </ul>
            )}
          </>
        )}
        {highlight === "dataPoints" && dpCount > 0 && (
          <ul className="mb-1.5 space-y-0.5">
            {meta.dataPoints.map((dp, i) => (
              <li key={i} className="text-[11px] text-gray-400">· {dp}</li>
            ))}
          </ul>
        )}
        {highlight === "emails" && emailCount > 0 && (
          <ul className="mb-1.5 space-y-0.5">
            {meta.emails.map((email, i) => (
              <li key={i} className="text-[11px] text-gray-400">
                <span className="font-medium">{email.name}</span>
                {email.subject && <span className="text-gray-300"> — {email.subject}</span>}
              </li>
            ))}
          </ul>
        )}

        {/* Count chips for other fields */}
        <div className="flex flex-wrap gap-1">
          {highlight !== "dataPoints" && dpCount > 0 && <Chip label={`${dpCount} data pts`} color="blue" />}
          {highlight !== "businessRule" && ecCount > 0 && <Chip label={`${ecCount} edge cases`} color="amber" />}
          {highlight !== "emails" && emailCount > 0 && <Chip label={`${emailCount} emails`} color="purple" />}
        </div>

        <p className="text-[10px] text-gray-300 mt-1.5">double-click to edit</p>
      </div>
    </div>
  );
}

function Chip({ label, color }: { label: string; color: "blue" | "amber" | "purple" }) {
  const cls = {
    blue: "bg-blue-50 text-blue-600",
    amber: "bg-amber-50 text-amber-600",
    purple: "bg-purple-50 text-purple-600",
  }[color];
  return <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium ${cls}`}>{label}</span>;
}

// ─── custom edge: labeled with click-to-edit ─────────────────────────────────

function LabeledEdge({
  id, sourceX, sourceY, targetX, targetY,
  sourcePosition, targetPosition, data, selected,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });
  const label = (data?.label as string) || "";
  const onEdit = data?.onEdit as ((id: string, label: string) => void) | undefined;
  const onDelete = data?.onDelete as ((id: string) => void) | undefined;

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: selected ? "#3b82f6" : "#94a3b8",
          strokeWidth: selected ? 2.5 : 1.5,
        }}
        markerEnd="url(#arrow)"
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: "absolute",
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: "all",
          }}
          className="nodrag nopan flex flex-col items-center gap-1"
        >
          {label ? (
            <div
              onClick={() => onEdit?.(id, label)}
              className="rounded-full bg-white border border-gray-300 px-2 py-0.5 text-[11px] text-gray-600 shadow-sm cursor-pointer hover:border-blue-400 hover:text-blue-600 max-w-[140px] text-center leading-tight"
            >
              {label}
            </div>
          ) : (
            <button
              onClick={() => onEdit?.(id, "")}
              className="w-5 h-5 rounded-full bg-white border border-dashed border-gray-300 text-gray-400 hover:border-blue-400 hover:text-blue-500 flex items-center justify-center text-xs"
              title="Add label"
            >
              +
            </button>
          )}
          {selected && (
            <button
              onClick={() => onDelete?.(id)}
              className="w-5 h-5 rounded-full bg-white border border-red-300 text-red-400 hover:bg-red-500 hover:text-white flex items-center justify-center text-xs shadow-sm transition-colors"
              title="Remove connection"
            >
              ×
            </button>
          )}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}

// ─── edge label editor popup ──────────────────────────────────────────────────

function EdgeEditPanel({
  edgeId, initialLabel, onSave, onDelete, onClose,
}: {
  edgeId: string;
  initialLabel: string;
  onSave: (id: string, label: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onClose: () => void;
}) {
  const [label, setLabel] = useState(initialLabel);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", h);
    return () => document.removeEventListener("keydown", h);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="bg-white rounded-xl shadow-xl p-5 w-80 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">Connection Label</h3>
        <input
          autoFocus
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") { setSaving(true); onSave(edgeId, label).then(() => { setSaving(false); onClose(); }); } }}
          placeholder="e.g. 50% convert, drop-off 10%..."
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
        />
        <div className="flex justify-between">
          <button
            onClick={async () => { await onDelete(edgeId); onClose(); }}
            className="text-xs text-red-500 hover:text-red-700"
          >
            Delete connection
          </button>
          <div className="flex gap-2">
            <button onClick={onClose} className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50">
              Cancel
            </button>
            <button
              onClick={async () => { setSaving(true); await onSave(edgeId, label); setSaving(false); onClose(); }}
              disabled={saving}
              className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── main JourneyGraph ────────────────────────────────────────────────────────

interface Props {
  tree: NodeTree;
  onSaveTouchpoint: (nodeId: string, name: string, metadata: TouchpointMetadata) => Promise<void>;
  onAddStage: (name: string, atIndex?: number) => Promise<void>;
  onDeleteStage: (stageId: string) => Promise<void>;
  onAddTouchpoint: (stageId: string, name: string) => Promise<void>;
  onDeleteTouchpoint: (tpId: string) => Promise<void>;
  onAddEdge: (sourceId: string, targetId: string) => Promise<void>;
  onSaveEdgeLabel: (edgeId: string, label: string) => Promise<void>;
  onRemoveEdge: (edgeId: string) => Promise<void>;
  onMoveNode: (nodeId: string, x: number, y: number, metadata: Record<string, unknown>) => Promise<void>;
}

export function JourneyGraph({ tree, onSaveTouchpoint, onAddStage, onDeleteStage, onAddTouchpoint, onDeleteTouchpoint, onAddEdge, onSaveEdgeLabel, onRemoveEdge, onMoveNode }: Props) {
  const { rfNodes: initNodes, rfEdges: initEdges } = buildLayout(tree);
  const [editingTp, setEditingTp] = useState<NodeRead | null>(null);
  const [editingEdge, setEditingEdge] = useState<{ id: string; label: string } | null>(null);
  const [addingStage, setAddingStage] = useState(false);
  const [stageName, setStageName] = useState("");
  const [highlight, setHighlight] = useState<Highlight>("feature");

  // Inject callbacks into node/edge data after building layout
  const nodesWithCallbacks: RFNode[] = initNodes.map((n) => {
    if (n.type === "touchpoint") {
      return { ...n, data: { ...n.data, onOpen: (node: NodeRead) => setEditingTp(node), onDelete: onDeleteTouchpoint, highlight } };
    }
    if (n.type === "stage") {
      return { ...n, data: { ...n.data, onAddTouchpoint, onDelete: onDeleteStage } };
    }
    return n;
  });
  const edgesWithCallbacks: RFEdge[] = initEdges.map((e) => ({
    ...e,
    data: {
      ...e.data,
      onEdit: (id: string, label: string) => setEditingEdge({ id, label }),
      onDelete: (id: string) => onRemoveEdge(id),
    },
  }));

  const [nodes, setNodes] = useNodesState(nodesWithCallbacks);
  const [edges, setEdges, onEdgesChange] = useEdgesState(edgesWithCallbacks);

  // Keep a ref so callbacks always see the latest tree without stale closures
  const treeRef = useRef(tree);
  useEffect(() => { treeRef.current = tree; }, [tree]);

  // Apply React Flow changes; restack touchpoints whenever a node's height changes
  const handleNodesChange = useCallback((changes: NodeChange[]) => {
    setNodes((prev) => {
      const next = applyNodeChanges(changes, prev);
      const hasDimChange = changes.some((c) => c.type === "dimensions");
      return hasDimChange ? restackTouchpoints(next, treeRef.current) : next;
    });
  }, []);

  // Rebuild nodes and edges whenever the tree or highlight mode changes
  useEffect(() => {
    const { rfNodes: n, rfEdges: e } = buildLayout(tree);
    const nwc = n.map((nd) => {
      if (nd.type === "touchpoint") return { ...nd, data: { ...nd.data, onOpen: (node: NodeRead) => setEditingTp(node), onDelete: onDeleteTouchpoint, highlight } };
      if (nd.type === "stage") return { ...nd, data: { ...nd.data, onAddTouchpoint, onDelete: onDeleteStage } };
      return nd;
    });
    const ewc = e.map((ed) => ({
      ...ed,
      data: {
        ...ed.data,
        onEdit: (id: string, label: string) => setEditingEdge({ id, label }),
        onDelete: (id: string) => onRemoveEdge(id),
      },
    }));
    setNodes(nwc);
    setEdges(ewc);
  }, [tree, highlight]);

  const onConnect = useCallback(
    async (connection: Connection) => {
      if (connection.source && connection.target) {
        await onAddEdge(connection.source, connection.target);
      }
    },
    [onAddEdge],
  );

  const onNodeDragStop = useCallback(
    async (_event: React.MouseEvent, rfNode: RFNode) => {
      // Only persist position for stages; touchpoints auto-stack
      if (rfNode.type === "stage") {
        const nodeData = rfNode.data.node as NodeRead;
        const meta = (nodeData.metadata as Record<string, unknown>) ?? {};
        await onMoveNode(rfNode.id, rfNode.position.x, rfNode.position.y, meta);
        // Restack touchpoints to sit below the stage's new position
        setNodes((prev) => restackTouchpoints(prev, treeRef.current));
      }
    },
    [onMoveNode],
  );

  const nodeTypes = { stage: StageNode, touchpoint: TouchpointNode };
  const edgeTypes = { labeled: LabeledEdge };

  const version = (tree.node.metadata as Record<string, string>)?.version;

  return (
    <div className="flex flex-col" style={{ height: "calc(100vh - 220px)" }}>
      <div className="mb-2 flex items-center gap-3 flex-wrap">
        <h2 className="text-lg font-bold text-gray-800">{tree.node.name}</h2>
        {version && <span className="text-xs text-gray-400">v{version}</span>}
        <span className="text-xs text-gray-400">— drag handles to connect · double-click touchpoint to edit</span>
        <div className="ml-auto flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-gray-400">Show:</span>
            <select
              value={highlight}
              onChange={(e) => setHighlight(e.target.value as Highlight)}
              className="rounded border border-gray-300 bg-white px-2 py-1 text-xs text-gray-600 focus:border-blue-400 focus:outline-none"
            >
              {HIGHLIGHT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          {addingStage ? (
            <>
              <input
                autoFocus
                value={stageName}
                onChange={(e) => setStageName(e.target.value)}
                onKeyDown={async (e) => {
                  if (e.key === "Enter" && stageName.trim()) { await onAddStage(stageName.trim()); setStageName(""); setAddingStage(false); }
                  if (e.key === "Escape") { setAddingStage(false); setStageName(""); }
                }}
                placeholder="Stage name…"
                className="rounded-lg border border-gray-300 px-2 py-1 text-sm focus:border-blue-400 focus:outline-none w-44"
              />
              <button
                onClick={async () => { if (stageName.trim()) { await onAddStage(stageName.trim()); setStageName(""); setAddingStage(false); } }}
                className="rounded-lg bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700"
              >Add</button>
              <button onClick={() => { setAddingStage(false); setStageName(""); }} className="text-xs text-gray-400 hover:text-gray-600">Cancel</button>
            </>
          ) : (
            <button
              onClick={() => setAddingStage(true)}
              className="rounded-lg border border-dashed border-gray-300 px-3 py-1 text-xs text-gray-500 hover:border-blue-400 hover:text-blue-600 transition-colors"
            >
              + Add Stage
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 rounded-xl border border-gray-200 overflow-hidden bg-gray-50">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeDragStop={onNodeDragStop}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          defaultEdgeOptions={{ type: "labeled" }}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          minZoom={0.2}
          maxZoom={2}
          deleteKeyCode={null}
        >
          <Controls />
          <MiniMap nodeStrokeWidth={3} zoomable pannable />
          <Background gap={20} color="#e5e7eb" />
          {/* arrowhead marker */}
          <svg style={{ position: "absolute", width: 0, height: 0 }}>
            <defs>
              <marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
              </marker>
            </defs>
          </svg>
        </ReactFlow>
      </div>

      {editingTp && (
        <TouchpointEditor
          name={editingTp.name}
          metadata={editingTp.metadata as unknown as TouchpointMetadata}
          onSave={async (name, metadata) => {
            await onSaveTouchpoint(editingTp.id, name, metadata);
            setEditingTp(null);
          }}
          onCancel={() => setEditingTp(null)}
        />
      )}

      {editingEdge && (
        <EdgeEditPanel
          edgeId={editingEdge.id}
          initialLabel={editingEdge.label}
          onSave={onSaveEdgeLabel}
          onDelete={onRemoveEdge}
          onClose={() => setEditingEdge(null)}
        />
      )}
    </div>
  );
}
