// api/UploadAndConversionPage/api.js
 import { request } from "../shared/request";
const DOC_BASE = import.meta.env.VITE_DOC_BASE || "http://localhost:5004";
const r = (path, opts) => request(DOC_BASE, path, opts);

/** GET /list-subfolders -> string[] */
 export async function listSubfolders() {
   return r(`/list-subfolders`);
 }

/** GET /list-files?folder=... -> string[] */
 export async function listFiles(folder) {
   return r(`/list-files?folder=${encodeURIComponent(folder || "")}`);
 }

/** POST /uploadpdfs (FormData) -> { job_id, message? } | 202 */
 export async function uploadPdfs(files, folder) {
   const fd = new FormData();
   fd.append("folder", folder);
   for (const f of files) fd.append("files", f);
   return r(`/uploadpdfs`, { method: "POST", body: fd });
 }

/** GET /job_status/:id -> { state, progress?, message?, done?, total? } */
 export async function getJobStatus(jobId) {
   return r(`/job_status/${encodeURIComponent(jobId)}`);
 }

/** POST /cancel_job/:id -> { status: "cancel_requested" | "already_finished" | "ok", state? } */
 export async function cancelJob(jobId) {
   return r(`/cancel_job/${encodeURIComponent(jobId)}`, { method: "POST" });
 }

// Optional export, falls du die Base-URL an anderer Stelle brauchst
export { DOC_BASE };