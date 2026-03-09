import { useState } from "react";
import type { NodeTree, TouchpointMetadata } from "../types";
import { TouchpointCard } from "./TouchpointCard";

interface Props {
  stageTree: NodeTree;
  onSaveTouchpoint: (nodeId: string, name: string, metadata: TouchpointMetadata) => Promise<void>;
  onAddTouchpoint: (stageId: string, name: string) => Promise<void>;
  onDeleteStage: (stageId: string) => Promise<void>;
  onDeleteTouchpoint: (tpId: string) => Promise<void>;
}

export function StageColumn({ stageTree, onSaveTouchpoint, onAddTouchpoint, onDeleteStage, onDeleteTouchpoint }: Props) {
  const [adding, setAdding] = useState(false);
  const [tpName, setTpName] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleAdd = async () => {
    if (!tpName.trim()) return;
    await onAddTouchpoint(stageTree.node.id, tpName.trim());
    setTpName("");
    setAdding(false);
  };

  const handleDeleteStage = async () => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    await onDeleteStage(stageTree.node.id);
  };

  return (
    <div className="flex-shrink-0 w-72 bg-gray-50 rounded-lg border border-gray-200">
      <div className="px-3 py-2 border-b border-gray-200 bg-gray-100 rounded-t-lg flex items-start justify-between group">
        <div>
          <h3 className="text-sm font-bold text-gray-700">{stageTree.node.name}</h3>
          <span className="text-[10px] text-gray-400">
            {stageTree.children.length} touchpoint{stageTree.children.length !== 1 ? "s" : ""}
          </span>
        </div>
        {confirmDelete ? (
          <div className="flex items-center gap-1 ml-2">
            <span className="text-[10px] text-red-600">Delete?</span>
            <button
              onClick={handleDeleteStage}
              className="rounded px-1.5 py-0.5 text-[10px] bg-red-600 text-white hover:bg-red-700"
            >
              Yes
            </button>
            <button
              onClick={() => setConfirmDelete(false)}
              className="rounded px-1.5 py-0.5 text-[10px] bg-gray-200 text-gray-600 hover:bg-gray-300"
            >
              No
            </button>
          </div>
        ) : (
          <button
            onClick={() => setConfirmDelete(true)}
            className="opacity-0 group-hover:opacity-100 ml-2 text-gray-400 hover:text-red-500 transition-all text-sm leading-none p-0.5 rounded hover:bg-red-50"
            title="Delete stage"
          >
            ×
          </button>
        )}
      </div>
      <div className="p-2 space-y-2 max-h-[calc(100vh-260px)] overflow-y-auto">
        {stageTree.children.map((tp) => (
          <TouchpointCard
            key={tp.node.id}
            tpTree={tp}
            onSave={onSaveTouchpoint}
            onDelete={onDeleteTouchpoint}
          />
        ))}

        {adding ? (
          <div className="rounded-lg border-2 border-dashed border-blue-300 bg-blue-50 p-2 space-y-2">
            <input
              autoFocus
              type="text"
              placeholder="Touchpoint name..."
              value={tpName}
              onChange={(e) => setTpName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAdd();
                if (e.key === "Escape") { setAdding(false); setTpName(""); }
              }}
              className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-400 focus:outline-none"
            />
            <div className="flex gap-2">
              <button onClick={handleAdd} className="rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700">
                Add
              </button>
              <button onClick={() => { setAdding(false); setTpName(""); }} className="rounded px-3 py-1 text-xs text-gray-500 hover:text-gray-700">
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setAdding(true)}
            className="w-full rounded-lg border-2 border-dashed border-gray-200 py-2 text-xs text-gray-400 hover:border-blue-300 hover:text-blue-500 hover:bg-blue-50/50 transition-colors"
          >
            + Add Touchpoint
          </button>
        )}
      </div>
    </div>
  );
}
