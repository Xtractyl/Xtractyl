import React, { useState } from "react";
import DinoLoader from "../components/DinoLoader.jsx";

export default function PDFUploadAndConversion() {
  const [files, setFiles] = useState([]);
  const [folder, setFolder] = useState("");
  const [fileStatuses, setFileStatuses] = useState([]);

  const handleFileChange = (e) => {
    setFiles([...e.target.files]);
  };

  const handleFolderChange = (e) => {
    setFolder(e.target.value.trim());
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!folder || files.length === 0) return;

    setFileStatuses([]); // Reset vorherige Status

    for (const file of files) {
      // 1. Ladeanzeige setzen
      setFileStatuses((prev) => [
        ...prev,
        { file: file.name, status: "loading" },
      ]);

      const formData = new FormData();
      formData.append("folder", folder);
      formData.append("files", file);

      try {
        const response = await fetch("http://localhost:5004/uploadpdfs", {
          method: "POST",
          body: formData,
        });

        const data = await response.json();
        const result = data.results?.[0] || {
          file: file.name,
          status: "error",
          message: "no response",
        };

        // 2. Status aktualisieren
        setFileStatuses((prev) =>
          prev.map((entry) =>
            entry.file === file.name ? result : entry
          )
        );
      } catch (error) {
        setFileStatuses((prev) =>
          prev.map((entry) =>
            entry.file === file.name
              ? { file: file.name, status: "error", message: error.message }
              : entry
          )
        );
      }
    }
  };

  return (
    <div className="p-6 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Upload and Convert Docs</h1>
      <p className="text-gray-600 mb-6">
        Select PDF files and specify a folder for HTML conversion.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block font-medium mb-1">
            Your subfolder (e.g. "oncology-july")
          </label>
          <input
            type="text"
            value={folder}
            onChange={handleFolderChange}
            placeholder="Enter subfolder name"
            required
            className="w-full p-2 border rounded"
          />
        </div>

        <div>
          <label className="block font-medium mb-1">Select your PDFs</label>
          <input
            type="file"
            accept="application/pdf"
            multiple
            onChange={handleFileChange}
            required
            className="w-full p-2 border rounded"
          />
          {files.length > 0 && (
            <p className="mt-2 text-sm text-gray-700">
              {files.length} file(s) selected
            </p>
          )}
        </div>

        <button
          type="submit"
          className="bg-[#6baa56] text-white px-4 py-2 rounded hover:bg-[#5b823f]"
        >
          Upload & Convert
        </button>
      </form>

      {fileStatuses.length > 0 && (
        <div className="mt-6 bg-[#cdc0a3] p-4 rounded shadow">
          <h2 className="font-semibold mb-2">Conversion Progress</h2>
          <ul className="list-disc pl-5">
            {fileStatuses.map((entry, index) => (
              <li key={index} className="flex items-center gap-2">
                <span className="font-mono">{entry.file}</span>
                {entry.status === "loading" ? (
                  <DinoLoader />
                ) : entry.status === "ok" ? (
                  <span className="text-green-700">✅ success</span>
                ) : (
                  <span className="text-red-600">❌ error – {entry.message}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}