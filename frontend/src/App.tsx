import { useState } from "react";
import { ExportGistModal } from "./components/ExportGistModal";
import { FileUpload } from "./components/FileUpload";
import { JourneyGraph } from "./components/JourneyGraph";
import { useJourney } from "./hooks/useJourney";
import { downloadDrawio } from "./lib/exportDrawio";
import { downloadJourneyJson } from "./lib/exportJson";
import type { TouchpointMetadata } from "./types";

export default function App() {
  const { roots, tree, loading, error, selectRoot, upload, saveNode, moveNode, addStage, deleteStage, addTouchpoint, deleteTouchpoint, addEdge, saveEdgeLabel, removeEdge, clearTree } =
    useJourney();
  const [showExport, setShowExport] = useState(false);

  const handleSaveTouchpoint = async (
    nodeId: string,
    name: string,
    metadata: TouchpointMetadata,
  ) => {
    await saveNode(nodeId, {
      name,
      metadata: metadata as unknown as Record<string, unknown>,
    });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-gray-900 px-4 py-3 flex items-center justify-between">
        <span className="text-sm font-semibold text-white">Journey Sonar</span>
        {tree && (
          <div className="flex items-center gap-2">
          <button
            onClick={() => downloadJourneyJson(tree)}
            className="flex items-center gap-1.5 rounded-lg border border-gray-600 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
          >
            <svg viewBox="0 0 16 16" className="w-3.5 h-3.5 fill-current" aria-hidden>
              <path d="M7.47 10.78a.75.75 0 001.06 0l3.75-3.75a.75.75 0 00-1.06-1.06L8.75 8.44V1.75a.75.75 0 00-1.5 0v6.69L4.78 5.97a.75.75 0 00-1.06 1.06l3.75 3.75zM1.75 12.5a.75.75 0 000 1.5h12.5a.75.75 0 000-1.5H1.75z"/>
            </svg>
            Download JSON
          </button>
          <button
            onClick={() => downloadDrawio(tree)}
            className="flex items-center gap-1.5 rounded-lg border border-gray-600 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
          >
            <svg viewBox="0 0 16 16" className="w-3.5 h-3.5 fill-current" aria-hidden>
              <path d="M1 2.5A1.5 1.5 0 012.5 1h3A1.5 1.5 0 017 2.5v1A1.5 1.5 0 015.5 5h-3A1.5 1.5 0 011 3.5v-1zM2.5 2a.5.5 0 00-.5.5v1a.5.5 0 00.5.5h3a.5.5 0 00.5-.5v-1a.5.5 0 00-.5-.5h-3zM9 2.5A1.5 1.5 0 0110.5 1h3A1.5 1.5 0 0115 2.5v1A1.5 1.5 0 0113.5 5h-3A1.5 1.5 0 019 3.5v-1zm1.5-.5a.5.5 0 00-.5.5v1a.5.5 0 00.5.5h3a.5.5 0 00.5-.5v-1a.5.5 0 00-.5-.5h-3zM1 10.5A1.5 1.5 0 012.5 9h3A1.5 1.5 0 017 10.5v1A1.5 1.5 0 015.5 13h-3A1.5 1.5 0 011 11.5v-1zm1.5-.5a.5.5 0 00-.5.5v1a.5.5 0 00.5.5h3a.5.5 0 00.5-.5v-1a.5.5 0 00-.5-.5h-3zM9 10.5A1.5 1.5 0 0110.5 9h3A1.5 1.5 0 0115 10.5v1A1.5 1.5 0 0113.5 13h-3A1.5 1.5 0 019 11.5v-1zm1.5-.5a.5.5 0 00-.5.5v1a.5.5 0 00.5.5h3a.5.5 0 00.5-.5v-1a.5.5 0 00-.5-.5h-3zM4 6.5a.5.5 0 01.5-.5h1a.5.5 0 010 1H5v1.5a.5.5 0 01-1 0V7h-.5a.5.5 0 01-.5-.5zM11.5 6a.5.5 0 000 1H12v1.5a.5.5 0 001 0V7h.5a.5.5 0 000-1h-2z"/>
            </svg>
            Export to draw.io
          </button>
          <button
            onClick={() => setShowExport(true)}
            className="flex items-center gap-1.5 rounded-lg border border-gray-600 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
          >
            <svg viewBox="0 0 16 16" className="w-3.5 h-3.5 fill-current" aria-hidden>
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
            </svg>
            Export to Gist
          </button>
          </div>
        )}
      </div>

      {error && (
        <div className="mx-4 mt-3 rounded bg-red-50 border border-red-200 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="p-4 space-y-4">
        {!tree && <FileUpload onUpload={upload} loading={loading} />}

        {!tree && roots.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-600 mb-2">
              Existing Journeys
            </h3>
            <div className="flex flex-wrap gap-2">
              {roots.map((root) => (
                <button
                  key={root.id}
                  onClick={() => selectRoot(root.id)}
                  className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:border-blue-300 transition-colors"
                >
                  {root.name}
                  <span className="ml-2 text-[10px] text-gray-400">
                    {new Date(root.created_at).toLocaleDateString()}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {tree && (
          <div>
            {roots.length > 1 && (
              <button
                onClick={clearTree}
                className="mb-3 text-xs text-blue-600 hover:underline"
              >
                Back to journey list
              </button>
            )}
            <JourneyGraph
              tree={tree}
              onSaveTouchpoint={handleSaveTouchpoint}
              onAddStage={addStage}
              onDeleteStage={deleteStage}
              onAddTouchpoint={addTouchpoint}
              onDeleteTouchpoint={deleteTouchpoint}
              onAddEdge={addEdge}
              onSaveEdgeLabel={saveEdgeLabel}
              onRemoveEdge={removeEdge}
              onMoveNode={moveNode}
            />
          </div>
        )}

        {!tree && roots.length === 0 && !loading && (
          <p className="text-center text-gray-400 text-sm py-8">
            Upload a journey JSON file to get started.
          </p>
        )}
      </div>
      {showExport && tree && (
        <ExportGistModal tree={tree} onClose={() => setShowExport(false)} />
      )}
    </div>
  );
}
