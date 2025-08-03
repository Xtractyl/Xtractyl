import React, { useEffect, useState } from "react";

// ---- Base URLs (adjust in one place) ----
const OLLAMA_BASE_URL = "http://localhost:11434";

export default function OllamaModelSelect({ value, onChange }) {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const fetchModels = async () => {
    setLoading(true);
    setErr("");
    try {
      const res = await fetch(`${OLLAMA_BASE_URL}/api/tags`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      // Shape: { models: [{ name, model, size, modified_at, ... }] }
      setModels(Array.isArray(data?.models) ? data.models : []);
    } catch (e) {
      setErr(
        "Failed to load models from Ollama."
      );
      setModels([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  return (
    <div className="w-full">
      <label className="block font-medium mb-1">Select Ollama model</label>

      <div className="flex gap-2">
        <select
          value={value || ""}
          onChange={(e) => onChange?.(e.target.value)}
          className="w-full p-2 border rounded"
        >
          <option value="">— Select a model —</option>
          {models.map((m) => (
            <option key={m.model || m.name} value={m.model || m.name}>
              {m.name || m.model}
            </option>
          ))}
        </select>

        <button
          type="button"
          onClick={fetchModels}
          className="px-3 py-2 rounded bg-gray-200 hover:bg-gray-300"
          disabled={loading}
        >
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {err && <p className="text-sm text-red-600 mt-2">{err}</p>}

      {/* Optional: allow manual entry if user knows a model tag */}
      <div className="mt-3">
        <label className="block text-sm mb-1">Or type a model tag</label>
        <input
          type="text"
          placeholder="e.g. gemma3:12b"
          value={value || ""}
          onChange={(e) => onChange?.(e.target.value)}
          className="w-full p-2 border rounded"
        />
      </div>
    </div>
  );
}