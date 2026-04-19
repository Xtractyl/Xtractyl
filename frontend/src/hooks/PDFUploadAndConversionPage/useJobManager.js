//src/hooks/PDFUploadAndConversionPage/useJobManager.js
import { useState, useEffect, useCallback } from "react";
import { uploadPdfs, getJobStatus, cancelJob } from "../../api/PDFUploadAndConversionPage/api";

export default function useJobManager(folder, files, refreshSubfolders, refreshFilesInFolder) {
  const [jobId, setJobId] = useState(() => localStorage.getItem("doclingJobId"));
  const [submitBusy, setSubmitBusy] = useState(false);
  const [serverMsg, setServerMsg] = useState("");
  const [jobStatus, setJobStatus] = useState(null);
  const [cancelBusy, setCancelBusy] = useState(false);

  // Restore jobId from localStorage
  useEffect(() => {
    if (!jobId) {
      const saved = localStorage.getItem("doclingJobId");
      if (saved) setJobId(saved);
    }
  }, [jobId]);

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
        const s = await getJobStatus(jobId);
        setJobStatus(s);

        if (["done", "error", "cancelled"].includes(s.state)) {
          localStorage.removeItem("doclingJobId");
          setJobId(null);
          return;
        }
        schedule();
      } catch (e) {
        if (e.status === 404) {
          localStorage.removeItem("doclingJobId");
          setJobId(null);
          setJobStatus(null);
          return;
        }
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

  // Cancel a running job
  const handleCancel = useCallback(async () => {
    if (!jobId) return;
    setCancelBusy(true);
    try {
      const data = await cancelJob(jobId);

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
      if (e?.status === 404) {
        localStorage.removeItem("doclingJobId");
        setJobId(null);
        setJobStatus(null);
        setServerMsg("⚠️ Job not found on server.");
      } else {
        setServerMsg(`❌ Failed to cancel job.`);
      }
    } finally {
      setCancelBusy(false);
    }
  }, [jobId]);

  // Submit PDFs
  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setServerMsg("");
    if (!folder || files.length === 0) return;

    setSubmitBusy(true);
    try {
      const data = await uploadPdfs(files, folder);
      setJobId(data.job_id);
      localStorage.setItem("doclingJobId", data.job_id);
      setServerMsg(data.message || "accepted");

      if (refreshSubfolders) refreshSubfolders();
      if (refreshFilesInFolder) refreshFilesInFolder(folder);
    } catch (err) {
  if (err?.status === 400) {
    setServerMsg("❌ Invalid input.");
  } else {
    setServerMsg("❌ Couldn't convert PDFs.");
  }
}
  }, [files, folder, refreshSubfolders, refreshFilesInFolder]);

  const clearJob = useCallback(() => {
    localStorage.removeItem("doclingJobId");
    setJobId(null);
    setServerMsg("");
    setJobStatus(null);
  }, []);

  return {
    jobId,
    jobStatus,
    serverMsg,
    submitBusy,
    cancelBusy,
    handleSubmit,
    handleCancel,
    clearJob
  };
}