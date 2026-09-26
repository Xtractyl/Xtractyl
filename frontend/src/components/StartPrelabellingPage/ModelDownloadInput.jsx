// src/components/ModelDownloadInput.jsx
import { useState } from "react";
import { useAppContext } from "../../context/AppContext";

export default function ModelDownloadInput({
  onDone
}) {
  const [name, setName] = useState("");
  const {
    pulling,
    pullingModel,
    pullProgress,
    pullError,
    startModelPull,
    resetPullError,
  } = useAppContext();

  const handlePull = async () => {
    const model = name.trim();
    if (!model) return;

    resetPullError();
    const ok = await startModelPull(model);
    if (ok) onDone?.(model);
  };

  const pullingThisModel = pulling && pullingModel === name.trim();
  const pullingOtherModel = pulling && pullingModel !== name.trim();

  return (
    <div className="space-y-3">
      <label className="block font-medium">
        Download new model with official names (
          <a
        
            href="https://ollama.com/library"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xtractyl-green hover:underline"
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
          className={`px-3 py-2 rounded ${pulling ? "opacity-60 cursor-not-allowed" : "bg-xtractyl-green text-xtractyl-white hover:bg-xtractyl-green/80 transition"}`}
        >
          {pullingThisModel ? "Pulling…" : "Download"}
        </button>
      </div>

      {pullingOtherModel && (
        <div className="text-sm text-xtractyl-outline">
          Still downloading "{pullingModel}" ({pullProgress})
        </div>
      )}
      {pullingThisModel && pullProgress && (
        <div className="text-sm text-xtractyl-outline">Progress: {pullProgress}</div>
      )}
      {!pulling && pullProgress === "Done" && pullingModel === name.trim() && (
        <div className="text-sm text-xtractyl-outline">Progress: Done</div>
      )}
      {pullError && <div className="text-sm text-xtractyl-orange">{pullError}</div>}

    </div>
  );
}