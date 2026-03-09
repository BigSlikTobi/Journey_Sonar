import { useEffect, useState } from "react";
import type { TouchpointMetadata } from "../types";

interface Props {
  name: string;
  metadata: TouchpointMetadata;
  onSave: (name: string, metadata: TouchpointMetadata) => Promise<void>;
  onCancel: () => void;
}

export function TouchpointEditor({ name, metadata, onSave, onCancel }: Props) {
  const [editName, setEditName] = useState(name);
  const [businessRule, setBusinessRule] = useState(metadata.businessRule || "");
  const [feature, setFeature] = useState(metadata.feature || "");
  const [dataPoints, setDataPoints] = useState<string[]>(metadata.dataPoints || []);
  const [edgeCases, setEdgeCases] = useState<string[]>(metadata.edgeCases || []);
  const [emails, setEmails] = useState<{ name: string; subject: string }[]>(metadata.emails || []);
  const [saving, setSaving] = useState(false);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onCancel(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onCancel]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(editName, {
        businessRule,
        feature,
        dataPoints: dataPoints.filter(Boolean),
        edgeCases: edgeCases.filter(Boolean),
        emails: emails.filter((e) => e.name || e.subject),
      });
    } finally {
      setSaving(false);
    }
  };

  const updateListItem = (list: string[], setList: (v: string[]) => void, i: number, v: string) => {
    const next = [...list];
    next[i] = v;
    setList(next);
  };

  return (
    // Backdrop
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onCancel(); }}
    >
      {/* Dialog */}
      <div className="relative w-full max-w-6xl max-h-[90vh] flex flex-col bg-white rounded-xl shadow-2xl">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-800">Edit Touchpoint</h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none w-7 h-7 flex items-center justify-center rounded hover:bg-gray-100"
          >
            ×
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 px-6 py-5">
          {/* Name — full width */}
          <div className="mb-5">
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Name</label>
            <input
              autoFocus
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-200"
            />
          </div>

          {/* Two-column grid */}
          <div className="grid grid-cols-2 gap-6">
            {/* Left column */}
            <div className="space-y-5">
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Business Rule</label>
                <textarea
                  value={businessRule}
                  onChange={(e) => setBusinessRule(e.target.value)}
                  rows={8}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-200 resize-y"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Feature</label>
                <textarea
                  value={feature}
                  onChange={(e) => setFeature(e.target.value)}
                  rows={6}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-200 resize-y"
                />
              </div>
            </div>

            {/* Right column */}
            <div className="space-y-5">
              <ListEditor
                label="Data Points"
                items={dataPoints}
                onChange={setDataPoints}
                onUpdate={(i, v) => updateListItem(dataPoints, setDataPoints, i, v)}
              />

              <ListEditor
                label="Edge Cases"
                items={edgeCases}
                onChange={setEdgeCases}
                onUpdate={(i, v) => updateListItem(edgeCases, setEdgeCases, i, v)}
              />

              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Emails</label>
                <div className="space-y-2">
                  {emails.map((email, i) => (
                    <div key={i} className="flex gap-2 items-center">
                      <input
                        placeholder="Name"
                        value={email.name}
                        onChange={(e) => {
                          const next = [...emails];
                          next[i] = { ...next[i], name: e.target.value };
                          setEmails(next);
                        }}
                        className="flex-1 rounded-lg border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-400 focus:outline-none"
                      />
                      <input
                        placeholder="Subject"
                        value={email.subject}
                        onChange={(e) => {
                          const next = [...emails];
                          next[i] = { ...next[i], subject: e.target.value };
                          setEmails(next);
                        }}
                        className="flex-1 rounded-lg border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-400 focus:outline-none"
                      />
                      <button
                        onClick={() => setEmails(emails.filter((_, j) => j !== i))}
                        className="text-red-400 hover:text-red-600 text-sm w-5 flex-shrink-0"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  onClick={() => setEmails([...emails, { name: "", subject: "" }])}
                  className="mt-2 text-xs text-blue-600 hover:underline"
                >
                  + Add email
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-xl">
          <button
            onClick={onCancel}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ListEditor({
  label,
  items,
  onChange,
  onUpdate,
}: {
  label: string;
  items: string[];
  onChange: (items: string[]) => void;
  onUpdate: (index: number, value: string) => void;
}) {
  return (
    <div>
      <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">{label}</label>
      <div className="space-y-1.5">
        {items.map((item, i) => (
          <div key={i} className="flex gap-2 items-center">
            <input
              value={item}
              onChange={(e) => onUpdate(i, e.target.value)}
              className="flex-1 rounded-lg border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-400 focus:outline-none"
            />
            <button
              onClick={() => onChange(items.filter((_, j) => j !== i))}
              className="text-red-400 hover:text-red-600 text-sm w-5 flex-shrink-0"
            >
              ×
            </button>
          </div>
        ))}
      </div>
      <button
        onClick={() => onChange([...items, ""])}
        className="mt-2 text-xs text-blue-600 hover:underline"
      >
        + Add {label.toLowerCase().replace(/s$/, "")}
      </button>
    </div>
  );
}
