// src/api/UploadTasksPage/api.js
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";

/** POST /upload_tasks -> { ...result } */
export async function uploadTasks({ projectName, token, htmlFolder }) {
  const res = await fetch(`${ORCH_BASE}/upload_tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_name: projectName,
      token,
      html_folder: htmlFolder,
    }),
  });

  if (!res.ok) {
    let msg = `Upload failed: ${res.status}`;
    try {
      const t = await res.text();
      if (t) msg += ` — ${t}`;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export async function getHtmlSubfolders() {
  const res = await fetch(`${ORCH_BASE}/list_html_subfolders`);
  if (!res.ok) throw new Error("Failed to fetch subfolders");
  return res.json();
}
