import React, { useState, useEffect } from "react";
import DinoLoader from "../components/DinoLoader.jsx";

export default function PDFUploadAndConversion() {
  const [files, setFiles] = useState([]);
  const [folder, setFolder] = useState("");
  const [fileStatuses, setFileStatuses] = useState([]);
  const [existingFolders, setExistingFolders] = useState([]);
  const [filesInSelectedFolder, setFilesInSelectedFolder] = useState([]);

  const fetchSubfolders = () => {
    fetch("http://localhost:5004/list-subfolders")
      .then((res) => res.json())
      .then((data) => setExistingFolders(data))
      .catch(() => setExistingFolders([]));
  };

  const fetchFilesInFolder = (folderName) => {
    fetch(`http://localhost:5004/list-files?folder=${folderName}`)
      .then((res) => res.json())
      .then((data) => setFilesInSelectedFolder(data))
      .catch(() => setFilesInSelectedFolder([]));
  };

  useEffect(() => {
    fetchSubfolders();
  }, []);

  useEffect(() => {
    if (!folder) return;
    fetchFilesInFolder(folder);
  }, [folder]);

  const handleFileChange = (e) => {
    setFiles([...e.target.files]);
  };

  const handleFolderChange = (e) => {
    setFolder(e.target.value.trim());
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!folder || files.length === 0) return;

    setFileStatuses([]);

    for (const file of files) {
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

    // 🔄 Nach Upload: Ordner und Dateiliste neu laden
    fetchSubfolders();
    fetchFilesInFolder(folder);
  };

  return (
    <div className="p-6 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Upload and Convert Docs</h1>
      <p className="text-gray-600 mb-6">
        Select PDF files and specify a folder for HTML conversion.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block font-medium mb-1">Choose or type a folder</label>
          <input
            list="folder-options"
            type="text"
            value={folder}
            onChange={handleFolderChange}
            placeholder="e.g. oncology-july"
            required
            className="w-full p-2 border rounded"
          />
          <datalist id="folder-options">
            {existingFolders.map((f, i) => (
              <option key={i} value={f} />
            ))}
          </datalist>
        </div>

        {existingFolders.length > 0 && (
          <div className="mt-4 bg-[#ede6d6] p-4 rounded">
            <h3 className="font-semibold mb-2">Existing folders:</h3>
            <ul className="list-disc pl-5 text-sm text-[#23211c]">
              {existingFolders.map((f, i) => (
                <li
                  key={i}
                  className={`cursor-pointer hover:underline ${
                    folder === f ? "font-bold text-[#6baa56]" : ""
                  }`}
                  onClick={() => setFolder(f)}
                >
                  📁 {f}
                </li>
              ))}
            </ul>
          </div>
        )}

        {filesInSelectedFolder.length > 0 && (
          <div className="mt-2 bg-[#ede6d6] p-4 rounded">
            <h3 className="font-semibold mb-2">Files in selected folder:</h3>
            <ul className="list-disc pl-5 text-sm text-[#23211c]">
              {filesInSelectedFolder.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </div>
        )}

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