// src/components/ModelDownloadInput.jsx
import React, { useState } from "react";

const OLLAMA_BASE = import.meta.env.VITE_OLLAMA_BASE || "http://localhost:11434";

export default function ModelDownloadInput({
  ollamaBase = OLLAMA_BASE,
  onDone,           
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
      const res = await fetch(`${ollamaBase}/api/pull`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: model }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`Pull failed: HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const obj = JSON.parse(line);
            if (typeof obj.total === "number" && typeof obj.completed === "number" && obj.total > 0) {
              const pct = Math.round((obj.completed / obj.total) * 100);
              setProgress(`${pct}%`);
            } else if (obj.status) {
              setProgress(obj.status);
            }
          } catch {
            // ignore partial lines
          }
        }
      }

      setProgress("Done");
      if (onDone) onDone(model);
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
          className={`px-3 py-2 rounded ${pulling ? "opacity-60 cursor-not-allowed" : "bg-[#6baa56] text-white hover:bg-[#5b823f]"}`}
        >
          {pulling ? "Pulling…" : "Download"}
        </button>
      </div>

      {progress && <div className="text-sm text-gray-700">Progress: {progress}</div>}
      {error && <div className="text-sm text-red-600">❌ {error}</div>}

    </div>
  );
}