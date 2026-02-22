// frontend/src/api/getResultsTable.js
export async function getResultsTable({ projectName, token }) {
  const baseUrl = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";
  const url = `${baseUrl}/results/table`;

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      project_name: projectName,
    }),
  });

  if (!res.ok) {
    let payload = null;
    try {
      payload = await res.json();
    } catch {
      // ignore, fall back to text
    }

    // New standardized error contract (ErrorResponse)
    if (payload && typeof payload === "object" && typeof payload.error === "string") {
      const err = new Error(payload.message || `Request failed: ${res.status}`);
      err.code = payload.error;
      err.status = res.status;
      err.details = Array.isArray(payload.details) ? payload.details : null;
      err.requestId = payload.request_id ?? null;
      throw err;
    }

    const text = await res.text().catch(() => "");
    const err = new Error(`Request failed: ${res.status} ${res.statusText} ${text || ""}`);
    err.status = res.status;
    throw err;
   }

  const json = await res.json();
  const data = json?.data ?? json?.logs ?? json ?? {};

  return {
    columns: Array.isArray(data.columns) ? data.columns : [],
    rows: Array.isArray(data.rows) ? data.rows : [],
    total: typeof data.total === "number" ? data.total : 0,
  };
}