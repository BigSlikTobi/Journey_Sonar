import { useCallback, useRef, useState } from "react";

interface Props {
  onUpload: (file: File) => void;
  loading: boolean;
}

export function FileUpload({ onUpload, loading }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      if (file.type === "application/json" || file.name.endsWith(".json")) {
        onUpload(file);
      }
    },
    [onUpload],
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
      onClick={() => inputRef.current?.click()}
      className={`cursor-pointer rounded-lg border-2 border-dashed p-6 text-center transition-colors ${
        dragOver
          ? "border-blue-400 bg-blue-50"
          : "border-gray-300 hover:border-gray-400"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".json"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />
      {loading ? (
        <p className="text-gray-500">Uploading...</p>
      ) : (
        <>
          <p className="text-gray-600 font-medium">Drop a journey JSON file here</p>
          <p className="text-gray-400 text-sm mt-1">or click to browse</p>
        </>
      )}
    </div>
  );
}
