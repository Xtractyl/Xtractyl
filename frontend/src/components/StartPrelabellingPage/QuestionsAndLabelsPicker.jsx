// src/components/QuestionsAndLabelsPicker.jsx
import React, { useEffect, useState } from "react";
import { listQalJsons, previewQal } from "../../api/StartPrelabellingPage/api.js";

export default function QuestionsAndLabelsPicker({
  projectName,                 // required to list files
  selectedFile,
  onChange,                    // (projectName, fileName, json)
  apiBase,                     // optional override; omit to use default
}) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [preview, setPreview] = useState(null);
  const [previewErr, setPreviewErr] = useState("");
  const [previewOpen, setPreviewOpen] = useState(false);

  useEffect(() => {
    if (!projectName) {
      setFiles([]);
      return;
    }

    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setErr("");
      try {
        const list = await listQalJsons(projectName, apiBase);
        if (!cancelled) setFiles(list);
      } catch (e) {
        if (!cancelled) setErr(e.message || "Failed to load files");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => { cancelled = true; };
  }, [projectName, apiBase]);

  const handlePreview = async (file) => {
    if (!projectName || !file) return;
    setPreview(null);
    setPreviewErr("");
    setPreviewOpen(true);
    try {
      const data = await previewQal(projectName, file, apiBase);
      setPreview(data);
    } catch (e) {
      setPreviewErr(e.message || "Failed to load preview");
    }
  };

  const handleFileSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const json = JSON.parse(text);
      onChange(projectName, file.name, json);
    } catch {
      alert("Invalid JSON file.");
    }
  };

  const handleDropdownSelect = async (fileName) => {
    if (!fileName || !projectName) return;
    try {
      const json = await previewQal(projectName, fileName, apiBase);
      onChange(projectName, fileName, json);
    } catch {
      alert("❌ Failed to load file content.");
    }
  };

  return (
    <div className="space-y-2">
      <label className="block font-medium">Questions & Labels (JSON in your project folder)</label>

      <div className="flex gap-2">
        <select
          value={selectedFile || ""}
          onChange={(e) => handleDropdownSelect(e.target.value)}
          className="w-full p-2 border rounded"
          disabled={!projectName || loading}
        >
          <option value="">{projectName ? "— Select JSON —" : "Select a project first"}</option>
          {files.map((f) => (
            <option key={f} value={f}>{f}</option>
          ))}
        </select>

        <button
          type="button"
          onClick={() => selectedFile && handlePreview(selectedFile)}
          disabled={!selectedFile}
          className={`px-3 py-2 rounded ${selectedFile ? "bg-xtractyl-green text-xtractyl-white hover:bg-xtractyl-green/80 transition" : "bg-xtractyl-offwhite text-xtractyl-outline/50 cursor-not-allowed"}`}
        >
          Preview
        </button>
      </div>  

      <div className="text-xs text-xtractyl-outline/60">
        Or upload a JSON file:
        <input type="file" accept="application/json" className="ml-2" onChange={handleFileSelect} />
      </div>

      {loading && <div className="text-sm text-xtractyl-outline/70">Loading…</div>}
      {err && <div className="text-sm text-xtractyl-orange">❌ {err}</div>}

      {previewOpen && (
        <div className="fixed inset-0 bg-xtractyl-darktext/40 flex items-center justify-center z-50">
          <div className="bg-xtractyl-white max-w-2xl w-full rounded shadow p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">Preview: {selectedFile}</h3>
              <button
                className="px-2 py-1 rounded text-xtractyl-white bg-xtractyl-green hover:bg-xtractyl-green/80"
                onClick={() => setPreviewOpen(false)}
              >
                Close
              </button>
            </div>
            <div className="max-h-[60vh] overflow-auto">
              {previewErr && <div className="text-sm text-xtractyl-orange mb-2">❌ {previewErr}</div>}
              {!preview && !previewErr && <div className="text-sm text-xtractyl-outline/70">Loading…</div>}
              {preview && (
                <pre className="text-xs whitespace-pre-wrap break-words">
                  {JSON.stringify(preview, null, 2)}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}