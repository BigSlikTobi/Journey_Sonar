import { useEffect, useRef, useState } from "react";
import type { NodeTree } from "../types";
import { generateMarkdown } from "../lib/exportMarkdown";
import { generateJourneyHtml } from "../lib/exportHtml";
import { postGist } from "../lib/github";

const TOKEN_KEY = "cjm_github_token";

interface Props {
  tree: NodeTree;
  onClose: () => void;
}

type Step = "form" | "exporting" | "done" | "error";

export function ExportGistModal({ tree, onClose }: Props) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) ?? "");
  const [step, setStep] = useState<Step>("form");
  const [gistUrl, setGistUrl] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", h);
    return () => document.removeEventListener("keydown", h);
  }, [onClose]);

  const handleExport = async () => {
    if (!token.trim()) { inputRef.current?.focus(); return; }
    localStorage.setItem(TOKEN_KEY, token.trim());
    setStep("exporting");

    try {
      const safeName = tree.node.name.toLowerCase().replace(/[^a-z0-9]+/g, "-");
      const htmlFilename = `${safeName}-journey.html`;
      const mdFilename = `${safeName}-journey.md`;
      const result = await postGist(
        token.trim(),
        tree.node.name,
        {
          [htmlFilename]: generateJourneyHtml(tree),
          [mdFilename]: generateMarkdown(tree),
        },
        htmlFilename,
      );
      setGistUrl(result.gistUrl);
      setPreviewUrl(result.previewUrl);
      setStep("done");
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Export failed");
      setStep("error");
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="w-full max-w-md bg-white rounded-xl shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <svg viewBox="0 0 16 16" className="w-5 h-5 text-gray-800 fill-current" aria-hidden>
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
            </svg>
            <h2 className="text-base font-semibold text-gray-800">Export to GitHub Gist</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl w-7 h-7 flex items-center justify-center rounded hover:bg-gray-100">
            ×
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          {step === "form" && (
            <>
              <p className="text-sm text-gray-500">
                A <strong>secret Gist</strong> (Markdown) will be created — only people with the link can view it.
              </p>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
                  GitHub Personal Access Token
                </label>
                <input
                  ref={inputRef}
                  type="password"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleExport(); }}
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                  autoFocus
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-200"
                />
                <p className="mt-1.5 text-xs text-gray-400">
                  Needs the <code className="bg-gray-100 px-1 rounded">gist</code> scope.{" "}
                  <a
                    href="https://github.com/settings/tokens/new?scopes=gist&description=Journey+Sonar"
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-500 hover:underline"
                  >
                    Create one →
                  </a>
                </p>
              </div>
              <div className="pt-1 text-xs text-gray-400">
                Journey: <span className="text-gray-600 font-medium">{tree.node.name}</span>
                {" · "}
                {tree.children.length} stages,{" "}
                {tree.children.reduce((s, c) => s + c.children.length, 0)} touchpoints
              </div>
            </>
          )}

          {step === "exporting" && (
            <div className="flex flex-col items-center py-6 gap-3">
              <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-gray-500">Generating and uploading…</p>
            </div>
          )}

          {step === "done" && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-green-600">
                <svg viewBox="0 0 20 20" className="w-5 h-5 fill-current flex-shrink-0">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-sm font-medium">Published!</span>
              </div>

              {/* Live preview URL — primary */}
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Live website</p>
                <div className="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2">
                  <a href={previewUrl} target="_blank" rel="noreferrer" className="flex-1 text-xs text-blue-600 hover:underline truncate font-mono">
                    {previewUrl}
                  </a>
                  <button
                    onClick={() => navigator.clipboard.writeText(previewUrl)}
                    className="flex-shrink-0 text-xs text-gray-400 hover:text-gray-700 px-2 py-1 rounded hover:bg-blue-100 transition-colors"
                    title="Copy link"
                  >
                    Copy
                  </button>
                </div>
              </div>

              <a
                href={previewUrl}
                target="_blank"
                rel="noreferrer"
                className="block w-full text-center rounded-lg bg-blue-600 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Open website ↗
              </a>

              {/* Gist source — secondary */}
              <a
                href={gistUrl}
                target="_blank"
                rel="noreferrer"
                className="block text-center text-xs text-gray-400 hover:text-gray-600 hover:underline"
              >
                View Gist source (HTML + Markdown)
              </a>
            </div>
          )}

          {step === "error" && (
            <div className="space-y-3">
              <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{errorMsg}</p>
              <button onClick={() => setStep("form")} className="text-xs text-blue-600 hover:underline">
                ← Try again
              </button>
            </div>
          )}
        </div>

        {(step === "form" || step === "error") && (
          <div className="flex justify-end gap-2 px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-xl">
            <button onClick={onClose} className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-100">
              Cancel
            </button>
            {step === "form" && (
              <button
                onClick={handleExport}
                disabled={!token.trim()}
                className="rounded-lg bg-gray-900 px-5 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-40"
              >
                Export →
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
