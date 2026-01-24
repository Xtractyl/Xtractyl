// src/components/ModelPicker.jsx
import React, { useEffect, useState } from "react";
import { listModels } from "../../api/StartPrelabellingPage/api.js";

export default function ModelPicker({
  ollamaBase,          // optional, defaults handled in api.js
  selectedModel,
  onChange,
  refreshKey,
}) {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setErr("");
      try {
        const names = await listModels();
        if (!cancelled) setModels(names);
      } catch (e) {
        if (!cancelled) setErr(e.message || "Failed to load models");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [ollamaBase, refreshKey]);

  return (
    <div className="space-y-2">
      <label className="block font-medium">Select installed model</label>

      <select
        value={selectedModel}
        onChange={(e) => onChange(e.target.value)}
        className="w-full p-2 border rounded"
      >
        <option value="">— Select a model —</option>
        {models.map((m) => (
          <option key={m} value={m}>{m}</option>
        ))}
      </select>

      <div className="flex items-center gap-2 text-xs  text-xtractyl-outline/60">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-3.5 w-3.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <polyline points="23 4 23 10 17 10" />
          <polyline points="1 20 1 14 7 14" />
          <path d="M3.51 9a9 9 0 0 1 14.88-3.36L23 10M1 14l4.61 4.36A9 9 0 0 0 20.49 15" />
        </svg>
        <span>
          After downloading a new model, <span className="whitespace-nowrap">refresh the page</span> to see it here.
        </span>
      </div>

      {loading && <div className="text-sm  text-xtractyl-outline/70">Loading models…</div>}
      {err && <div className="text-sm text-xtractyl-orange">❌ {err}</div>}
    </div>
  );
}