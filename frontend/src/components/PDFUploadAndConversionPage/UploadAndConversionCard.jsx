// src/components/UploadAndConvertCard.jsx
import React, { useState } from "react";
import useSubfolders from "../../hooks/PDFUploadAndConversionPage/useSubfolders";
import useFilesInFolder from "../../hooks/PDFUploadAndConversionPage/useFilesInFolder";
import useJobManager from "../../hooks/PDFUploadAndConversionPage/useJobManager";

export default function UploadAndConvertCard() {
  const [files, setFiles] = useState([]);
  const [folder, setFolder] = useState("");

  const {
    existingFolders,
    loadingFolders,
    foldersError,
    refreshSubfolders
  } = useSubfolders();

  const {
    filesInSelectedFolder,
    loadingFiles,
    filesError,
    refreshFilesInFolder
  } = useFilesInFolder(folder, existingFolders, 300);

  const {
    jobId, jobStatus, serverMsg, submitBusy, cancelBusy,
    handleSubmit, handleCancel, clearJob
  } = useJobManager(folder, files, refreshSubfolders, refreshFilesInFolder);

  const handleFileChange = (e) => setFiles([...e.target.files]);
  const handleFolderChange = (e) => setFolder(e.target.value.trim());

  return (
    <div className="p-6 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Upload and Convert Docs</h1>
      <p className="text-gray-600 mb-6">
        Select PDF files and specify a working folder for HTML conversion.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block font-medium mb-1">Type in the name for a new folder or that of an existing folder</label>
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

        {loadingFolders && <div className="text-sm">Loading folders…</div>}
        {foldersError && <div className="text-sm text-red-600">Failed to load folders.</div>}

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

        {loadingFiles && <div className="text-sm mt-2">Loading files…</div>}
        {filesError && <div className="text-sm text-red-600 mt-2">Failed to load files.</div>}

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
          disabled={submitBusy || !!jobId}
          className={`bg-[#6baa56] text-white px-4 py-2 rounded hover:bg-[#5b823f] ${
            submitBusy || jobId ? "opacity-60 cursor-not-allowed" : ""
          }`}
        >
          {submitBusy ? "Submitting…" : jobId ? "Job running…" : "Upload & Convert"}
        </button>

        {serverMsg && <p className="text-sm mt-2">{serverMsg}</p>}
      </form>

      {/* Status panel */}
      {jobId && jobStatus && (
        <div className="mt-4 bg-[#cdc0a3] p-4 rounded">
          <div className="font-medium mb-1">
            Status: {jobStatus.state}{" "}
            {typeof jobStatus.progress === "number"
              ? `— ${Math.round((jobStatus.progress || 0) * 100)}%`
              : ""}
          </div>
          <div className="w-full h-2 bg-gray-200 rounded">
            <div
              className="h-2 bg-[#6baa56] rounded"
              style={{ width: `${Math.round((jobStatus.progress || 0) * 100)}%` }}
            />
          </div>
          {jobStatus.message && <div className="text-sm mt-2">{jobStatus.message}</div>}
          <div className="text-xs text-gray-600 mt-1">
            {jobStatus.done ?? 0}/{jobStatus.total ?? 0} files
          </div>
        </div>
      )}

      {/* Active job controls */}
      {jobId && (
        <div className="mt-6 bg-[#ede6d6] p-4 rounded">
          <div className="font-semibold">Active conversion job</div>
          <div className="text-sm break-all">Job ID: {jobId}</div>

          <div className="mt-3 flex gap-3">
            <button
              type="button"
              onClick={handleCancel}
              disabled={cancelBusy}
              className={`px-3 py-2 rounded bg-red-600 text-white hover:bg-red-700 ${
                cancelBusy ? "opacity-60 cursor-not-allowed" : ""
              }`}
            >
              {cancelBusy ? "Cancelling…" : "Cancel Job"}
            </button>

            <button
              type="button"
              className="px-3 py-2 rounded bg-gray-200 hover:bg-gray-300"
              onClick={clearJob}
            >
              Clear Job ID (local)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}