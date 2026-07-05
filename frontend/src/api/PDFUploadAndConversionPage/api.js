// api/PDFUploadAndConversionPage/api.js
import { request } from "../shared/request";
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";
const r = (path, opts) => request(ORCH_BASE, path, opts);

/** POST /conversion/prepare -> { job_id, presigned_urls: [{filename, upload_url, pdf_key}] } */
export async function prepareConversion(projectName, filenames) {
  return r(`/conversion/prepare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project: projectName, filenames }),
  });
}

/** PUT presigned URL -> upload file directly to MinIO */
export async function uploadToMinio(uploadUrl, file) {
  const res = await fetch(uploadUrl, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": "application/pdf" },
  });
  if (!res.ok) throw new Error(`MinIO upload failed for ${file.name}: ${res.status}`);
}

/** POST /conversion/convert -> { job_id, status } */
export async function startConversion(jobId) {
  return r(`/conversion/convert`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId }),
  });
}

/** GET /conversion/status/:job_id -> { job_id, status, total_files, converted_files, error? } */
export async function getConversionStatus(jobId) {
  return r(`/conversion/status/${encodeURIComponent(jobId)}`);
}