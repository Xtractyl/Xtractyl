// src/components/QuestionsAndLabelsPicker.jsx
import React, { useEffect, useState } from "react";

export default function QuestionsAndLabelsPicker({
  apiBase = "http://localhost:5001",
  projectName,                 // required to list files
  selectedFile,
  onChange,                    // (projectName, fileName)
}) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [preview, setPreview] = useState(null);
  const [previewErr, setPreviewErr] = useState("");
  const [previewOpen, setPreviewOpen] = useState(false);
  const [questionsAndLabels, setQuestionsAndLabels] = useState(null);

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
        const res = await fetch(
          `${apiBase}/list_qal_jsons?project=${encodeURIComponent(projectName)}`
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled) setFiles(Array.isArray(data) ? data : []);
      } catch (e) {
        if (!cancelled) setErr(e.message || "Failed to load files");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [apiBase, projectName]);

  const handlePreview = async (file) => {
    if (!projectName || !file) return;
    setPreview(null);
    setPreviewErr("");
    setPreviewOpen(true);
    try {
      const url = `${apiBase}/preview_qal?project=${encodeURIComponent(projectName)}&file=${encodeURIComponent(file)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPreview(data);
    } catch (e) {
      setPreviewErr(e.message || "Failed to load preview");
    }
  };
  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const text = await file.text();
    try {
      const json = JSON.parse(text);
      onChange(projectName, file.name, json); // <- übergib auch das JSON
    } catch (err) {
      alert("Invalid JSON file.");
    }
  };

  const handleDropdownSelect = async (fileName) => {
    if (!fileName || !projectName) return;
    try {
      const res = await fetch(
        `${apiBase}/preview_qal?project=${encodeURIComponent(projectName)}&file=${encodeURIComponent(fileName)}`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      onChange(projectName, fileName, json);
    } catch (err) {
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
          className={`px-3 py-2 rounded ${selectedFile ? "bg-gray-200 hover:bg-gray-300" : "bg-gray-100 text-gray-400 cursor-not-allowed"}`}
        >
          Preview
        </button>
      </div>
      {loading && <div className="text-sm text-gray-600">Loading…</div>}
      {err && <div className="text-sm text-red-600">❌ {err}</div>}

      {/* Simple preview modal */}
      {previewOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white max-w-2xl w-full rounded shadow p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">Preview: {selectedFile}</h3>
              <button
                className="px-2 py-1 rounded bg-gray-200 hover:bg-gray-300"
                onClick={() => setPreviewOpen(false)}
              >
                Close
              </button>
            </div>
            <div className="max-h-[60vh] overflow-auto">
              {previewErr && <div className="text-sm text-red-600 mb-2">❌ {previewErr}</div>}
              {!preview && !previewErr && <div className="text-sm text-gray-600">Loading…</div>}
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