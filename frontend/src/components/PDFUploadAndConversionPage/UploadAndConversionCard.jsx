import React, { useState, useEffect } from "react";
import {
    listSubfolders,
    listFiles,
    uploadPdfs,
    getJobStatus,
    cancelJob
  } from "../../api/PDFUploadAndConversionPage/api.js";

export default function UploadAndConvertCard() {
  // --- UI state ---
  const [files, setFiles] = useState([]);
  const [folder, setFolder] = useState("");
  const [existingFolders, setExistingFolders] = useState([]);
  const [filesInSelectedFolder, setFilesInSelectedFolder] = useState([]);

  // --- job / server interaction state ---
  const [jobId, setJobId] = useState(() => localStorage.getItem("doclingJobId"));
  const [submitBusy, setSubmitBusy] = useState(false);
  const [serverMsg, setServerMsg] = useState("");
  const [jobStatus, setJobStatus] = useState(null);
  const [cancelBusy, setCancelBusy] = useState(false);

  // Fetch existing subfolders
  const fetchSubfolders = () => {
    listSubfolders()
      .then((data) => setExistingFolders(data))
      .catch(() => setExistingFolders([]));
  };

  // Fetch list of PDFs in a selected folder
  const fetchFilesInFolder = (folderName) => {
    listFiles(folderName)
      .then((data) => setFilesInSelectedFolder(data))
      .catch(() => setFilesInSelectedFolder([]));
  };

  // Cancel a running job
const handleCancel = async () => {
    if (!jobId) return;
    setCancelBusy(true);
    try {
      const data = await cancelJob(jobId); // data ist schon das JSON
  
      if (data.status === "already_finished") {
        setServerMsg(`ℹ️ Job already ${data.state}.`);
        localStorage.removeItem("doclingJobId");
        setJobId(null);
        return;
      }
  
      if (data.status === "cancel_requested") {
        setServerMsg("🛑 Cancel requested.");
        setJobStatus((prev) => ({ ...(prev || {}), state: "cancelling", message: "cancel requested" }));
        return;
      }
  
      setServerMsg("ℹ️ Cancel processed.");
    } catch (e) {
      if (e.status === 404) {
        localStorage.removeItem("doclingJobId");
        setJobId(null);
        setJobStatus(null);
        setServerMsg("⚠️ Job not found on server.");
      } else {
        console.error(e);
        setServerMsg(`❌ ${e.message}`);
      }
    } finally {
      setCancelBusy(false);
    }
  };

  // Restore job id from localStorage if empty
  useEffect(() => {
    if (!jobId) {
      const saved = localStorage.getItem("doclingJobId");
      if (saved) setJobId(saved);
    }
  }, [jobId]);

  // Load folders initially
  useEffect(() => {
    fetchSubfolders();
  }, []);

  // Load files when the selected folder changes
  useEffect(() => {
    if (folder) fetchFilesInFolder(folder);
  }, [folder]);

  // Poll job status
  useEffect(() => {
    if (!jobId) return;

    let cancelled = false;
    let timer = null;

    const schedule = (ms = 1500) => {
      if (!cancelled) timer = setTimeout(tick, ms);
    };

    const tick = async () => {
        try {
          const s = await getJobStatus(jobId); // direktes JSON-Objekt
      
          setJobStatus(s);
      
          if (["done", "error", "cancelled"].includes(s.state)) {
            localStorage.removeItem("doclingJobId");
            setJobId(null);
            return;
          }
          schedule();
        } catch (e) {
          if (e.status === 404) {
            // Stale jobId → clean up
            localStorage.removeItem("doclingJobId");
            setJobId(null);
            setJobStatus(null);
            return;
          }
      
          // alle anderen Fehler: einfach weiter pollen
          setJobStatus((s) => s ?? { state: "queued", message: "waiting…" });
          schedule();
        }
      };

    tick();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [jobId]);

  const handleFileChange = (e) => setFiles([...e.target.files]);
  const handleFolderChange = (e) => setFolder(e.target.value.trim());

// Submit PDFs to the server
const handleSubmit = async (e) => {
    e.preventDefault();
    setServerMsg("");
    if (!folder || files.length === 0) return;
  
    setSubmitBusy(true);
    try {
      const data = await uploadPdfs(files, folder); // API-Funktion nutzen
  
      setJobId(data.job_id);
      localStorage.setItem("doclingJobId", data.job_id);
      setServerMsg(data.message || "accepted");
  
      fetchSubfolders();
      fetchFilesInFolder(folder);
    } catch (err) {
      console.error(err);
      setServerMsg(`❌ ${err.message}`);
    } finally {
      setSubmitBusy(false);
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
          <label className="block font-medium mb-1">Type in folder name</label>
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
              onClick={() => {
                localStorage.removeItem("doclingJobId");
                setJobId(null);
                setServerMsg("");
                setJobStatus(null);
              }}
            >
              Clear Job ID (local)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}