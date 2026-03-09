import { useState } from "react";
import type { NodeTree, TouchpointMetadata } from "../types";
import { TouchpointEditor } from "./TouchpointEditor";

interface Props {
  tpTree: NodeTree;
  onSave: (nodeId: string, name: string, metadata: TouchpointMetadata) => Promise<void>;
  onDelete: (tpId: string) => Promise<void>;
}

export function TouchpointCard({ tpTree, onSave, onDelete }: Props) {
  const [editing, setEditing] = useState(false);
  const { node } = tpTree;
  const meta = node.metadata as unknown as TouchpointMetadata;

  // Editor renders as a portal-style overlay, card stays mounted underneath

  const dataPointCount = meta.dataPoints?.length ?? 0;
  const edgeCaseCount = meta.edgeCases?.length ?? 0;
  const emailCount = meta.emails?.length ?? 0;

  return (
    <>
    {editing && (
      <TouchpointEditor
        name={node.name}
        metadata={meta}
        onSave={async (name, metadata) => {
          await onSave(node.id, name, metadata);
          setEditing(false);
        }}
        onCancel={() => setEditing(false)}
      />
    )}
    <div
      className="group relative cursor-pointer rounded-lg border border-gray-200 bg-white p-3 shadow-sm hover:border-blue-300 hover:shadow transition-all"
      onClick={() => setEditing(true)}
    >
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(node.id); }}
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-500 transition-all text-base leading-none w-4 h-4 flex items-center justify-center rounded hover:bg-red-50"
        title="Delete touchpoint"
      >
        ×
      </button>
      <h4 className="text-sm font-semibold text-gray-800 mb-1 pr-4">{node.name}</h4>

      {meta.businessRule && (
        <p className="text-xs text-gray-500 line-clamp-2 mb-1">{meta.businessRule}</p>
      )}
      {meta.feature && (
        <p className="text-xs text-gray-400 line-clamp-1 mb-2">{meta.feature}</p>
      )}

      <div className="flex flex-wrap gap-1.5">
        {dataPointCount > 0 && (
          <Badge label={`${dataPointCount} data point${dataPointCount > 1 ? "s" : ""}`} />
        )}
        {edgeCaseCount > 0 && (
          <Badge label={`${edgeCaseCount} edge case${edgeCaseCount > 1 ? "s" : ""}`} color="amber" />
        )}
        {emailCount > 0 && (
          <Badge label={`${emailCount} email${emailCount > 1 ? "s" : ""}`} color="purple" />
        )}
      </div>
    </div>
    </>
  );
}

function Badge({ label, color = "blue" }: { label: string; color?: string }) {
  const colors: Record<string, string> = {
    blue: "bg-blue-50 text-blue-700",
    amber: "bg-amber-50 text-amber-700",
    purple: "bg-purple-50 text-purple-700",
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${colors[color]}`}>
      {label}
    </span>
  );
}
