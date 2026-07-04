// src/components/UploadAndConvertCard.jsx
import { useState } from "react";
import useJobManager from "../../hooks/PDFUploadAndConversionPage/useJobManager";
import { useAppContext } from "../../context/AppContext";

export default function UploadAndConversionCard() {
  const [files, setFiles] = useState([]);

  const { projectName, saveProjectName } = useAppContext();

  const { jobId, jobStatus, serverMsg, submitBusy, handleSubmit} = useJobManager(projectName, files);


  const handleFileChange = (e) => setFiles([...e.target.files]);

  return (
    <div className="p-6 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
      <h1 className="text-2xl font-semibold mb-4">Upload and Convert Docs</h1>
      <p className="text-xtractyl-outline/70 mb-6">
        Enter a project name and select PDFs to convert.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block font-medium mb-1">Project name</label>
          <input
            type="text"
            value={projectName}
            onChange={(e) => saveProjectName(e.target.value.trim())}
            placeholder="e.g. oncology-july"
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
            <p className="mt-2 text-sm text-xtractyl-outline">
              {files.length} file(s) selected
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={submitBusy || !!jobId}
          className={`bg-xtractyl-green text-xtractyl-white px-4 py-2 rounded hover:bg-xtractyl-green/80 transition ${            submitBusy || jobId ? "opacity-60 cursor-not-allowed" : ""
          }`}
        >
          {submitBusy ? "Submitting…" : jobId ? "Job running…" : "Upload & Convert"}
        </button>

        {serverMsg && <p className="text-sm mt-2">{serverMsg}</p>}
      </form>

      {/* Status panel */}
      {jobId && jobStatus && (
        <div className="mt-4 bg-xtractyl-offwhite p-4 rounded">
          <div className="font-medium mb-1">
            Status: {jobStatus.status}{" "}
            {jobStatus.total_files > 0 ? `— ${jobStatus.converted_files ?? 0}/${jobStatus.total_files} files` : ""}
          </div>
          <div className="w-full h-2 bg-xtractyl-offwhite rounded">
            <div
              className="h-2 bg-xtractyl-green rounded"
             style={{ width: `${Math.round(((jobStatus.converted_files ?? 0) / (jobStatus.total_files || 1)) * 100)}%` }}
            />
          </div>
          </div>
      )}

      {/* Active job controls */}
      {jobId && (
        <div className="mt-6 bg-xtractyl-offwhite p-4 rounded">
          <div className="font-semibold">Active conversion job</div>
          <div className="text-sm break-all">Job ID: {jobId}</div>

          <div className="mt-3 flex gap-3">
          </div>
        </div>
      )}
    </div>
  );
}