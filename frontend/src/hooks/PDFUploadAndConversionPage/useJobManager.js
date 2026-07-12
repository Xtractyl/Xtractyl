//src/hooks/PDFUploadAndConversionPage/useJobManager.js
import { useState, useEffect, useCallback } from "react";
import { prepareConversion, discardConversion, uploadToMinio, startConversion, getConversionStatus } from "../../api/PDFUploadAndConversionPage/api";

export default function useJobManager(projectName, files) {
  const [jobId, setJobId] = useState(() => localStorage.getItem("conversionJobId"));
  const [submitBusy, setSubmitBusy] = useState(false);
  const [serverMsg, setServerMsg] = useState("");
  const [jobStatus, setJobStatus] = useState(null);

  // Restore jobId from localStorage
  useEffect(() => {
    if (!jobId) {
      const saved = localStorage.getItem("conversionJobId");
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
        const s = await getConversionStatus(jobId);
        setJobStatus(s);

        if (["done", "error", "cancelled"].includes(s.status)) {
          localStorage.removeItem("conversionJobId");
          setJobId(null);
          setServerMsg(s.status === "done" ? "✅ Conversion complete." : `❌ Conversion ${s.status}.`);
          return;
        }
        schedule();
      } catch (e) {
        if (e.status === 404) {
          localStorage.removeItem("conversionJobId");
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

  // Submit PDFs
    const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setServerMsg("");
    if (!projectName || files.length === 0) return;
    setSubmitBusy(true);
    let job_id;
    try {
      // 1. Prepare: get presigned URLs
      const filenames = files.map((f) => f.name);
      const prep = await prepareConversion(projectName, filenames);
      job_id = prep.job_id;
      const presigned_urls = prep.presigned_urls;

      // 2. Upload each file directly to MinIO
      await Promise.all(
        presigned_urls.map(({ upload_url, filename }) => {
          const file = files.find((f) => f.name === filename);
          return uploadToMinio(upload_url, file);
        })
      );

      // 3. Trigger conversion
      await startConversion(job_id);

      // 4. Start polling
      setJobId(job_id);
      localStorage.setItem("conversionJobId", job_id);
      setServerMsg("✅ Upload complete, conversion started.");
    } catch (err) {
      if (job_id) {
        try {
          await discardConversion(job_id);
        } catch {
          /* best effort, ignore */
        }
      }
      setServerMsg(`❌ ${err.message || "Couldn't start conversion."}`);
    } finally {
      setSubmitBusy(false);
    }
  }, [files, projectName]);

  return { jobId, jobStatus, serverMsg, submitBusy, handleSubmit};
}