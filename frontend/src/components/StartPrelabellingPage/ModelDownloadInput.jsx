// src/components/ModelDownloadInput.jsx
import React, { useState } from "react";
import { pullModel } from "../../api/StartPrelabellingPage/api.js";

export default function ModelDownloadInput({
  onDone           
}) {
  const [name, setName] = useState("");
  const [pulling, setPulling] = useState(false);
  const [progress, setProgress] = useState("");
  const [error, setError] = useState("");

  const handlePull = async () => {
    const model = name.trim();
    if (!model) return;
  
    setPulling(true);
    setProgress("Starting…");
    setError("");
  
    try {
      await pullModel(model, setProgress);
      setProgress("Done");
      onDone?.(model);
    } catch (e) {
      setError(e.message || "Unknown error");
    } finally {
      setPulling(false);
    }
  };

  return (
    <div className="space-y-3">
      <label className="block font-medium">
        Download new model with official names (
        <a
            href="https://ollama.com/library"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#6baa56] hover:underline"
        >
            official names
        </a>
        )
        </label>
      <div className="flex gap-2">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder='e.g. "gemma:2b" or "llama3.1:8b"'
          className="w-full p-2 border rounded"
          disabled={pulling}
        />
        <button
          type="button"
          onClick={handlePull}
          disabled={!name.trim() || pulling}
          className={`px-3 py-2 rounded ${pulling ? "opacity-60 cursor-not-allowed" : "bg-xtractyl-green text-white hover:bg-xtractyl-green"}`}
        >
          {pulling ? "Pulling…" : "Download"}
        </button>
      </div>

      {progress && <div className="text-sm text-gray-700">Progress: {progress}</div>}
      {error && <div className="text-sm text-red-600">❌ {error}</div>}

    </div>
  );
}