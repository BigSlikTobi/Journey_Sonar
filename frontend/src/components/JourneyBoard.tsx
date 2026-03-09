import { useState } from "react";
import type { NodeTree, TouchpointMetadata } from "../types";
import { StageColumn } from "./StageColumn";

interface Props {
  tree: NodeTree;
  onSaveTouchpoint: (nodeId: string, name: string, metadata: TouchpointMetadata) => Promise<void>;
  onAddStage: (name: string, atIndex: number) => Promise<void>;
  onDeleteStage: (stageId: string) => Promise<void>;
  onAddTouchpoint: (stageId: string, name: string) => Promise<void>;
  onDeleteTouchpoint: (tpId: string) => Promise<void>;
}

function InsertZone({ atIndex, onAdd }: { atIndex: number; onAdd: (name: string, at: number) => Promise<void> }) {
  const [active, setActive] = useState(false);
  const [name, setName] = useState("");

  const commit = async () => {
    if (!name.trim()) return;
    await onAdd(name.trim(), atIndex);
    setName("");
    setActive(false);
  };

  if (active) {
    return (
      <div className="flex-shrink-0 w-60 self-start rounded-lg border-2 border-dashed border-blue-400 bg-blue-50 p-3 space-y-2 mt-0">
        <input
          autoFocus
          type="text"
          placeholder="Stage name..."
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") commit();
            if (e.key === "Escape") { setActive(false); setName(""); }
          }}
          className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-400 focus:outline-none"
        />
        <div className="flex gap-2">
          <button onClick={commit} className="rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700">
            Add
          </button>
          <button onClick={() => { setActive(false); setName(""); }} className="rounded px-3 py-1 text-xs text-gray-500 hover:text-gray-700">
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <button
      onClick={() => setActive(true)}
      className="flex-shrink-0 self-stretch w-8 flex items-center justify-center group"
      title="Insert stage here"
    >
      <div className="w-px h-full bg-gray-200 group-hover:bg-blue-300 relative flex items-center justify-center transition-colors">
        <span className="absolute w-5 h-5 rounded-full bg-white border-2 border-gray-300 group-hover:border-blue-400 group-hover:text-blue-500 flex items-center justify-center text-gray-400 text-xs font-bold transition-colors">
          +
        </span>
      </div>
    </button>
  );
}

export function JourneyBoard({ tree, onSaveTouchpoint, onAddStage, onDeleteStage, onAddTouchpoint, onDeleteTouchpoint }: Props) {
  const version = (tree.node.metadata as Record<string, string>)?.version;

  return (
    <div>
      <div className="mb-4">
        <h2 className="text-lg font-bold text-gray-800">{tree.node.name}</h2>
        {version && <span className="text-xs text-gray-400">v{version}</span>}
      </div>
      <div className="flex items-start overflow-x-auto pb-4 gap-0">
        <InsertZone atIndex={0} onAdd={onAddStage} />
        {tree.children.map((stage, index) => (
          <>
            <StageColumn
              key={stage.node.id}
              stageTree={stage}
              onSaveTouchpoint={onSaveTouchpoint}
              onAddTouchpoint={onAddTouchpoint}
              onDeleteStage={onDeleteStage}
              onDeleteTouchpoint={onDeleteTouchpoint}
            />
            <InsertZone atIndex={index + 1} onAdd={onAddStage} />
          </>
        ))}
        {/* Append at end */}
        {tree.children.length === 0 && (
          <InsertZone atIndex={0} onAdd={onAddStage} />
        )}
      </div>
    </div>
  );
}
