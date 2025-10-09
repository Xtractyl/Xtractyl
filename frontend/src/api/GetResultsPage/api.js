// frontend/src/api/getResultsTable.js
export async function getResultsTable({ projectName, token, limit = 50, offset = 0 }) {
  const baseUrl = import.meta.env.VITE_ORCH_URL || "http://localhost:5001";
  const url = `${baseUrl}/get_results_table`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_name: projectName,
      token,
      limit,
      offset,
    }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Request failed: ${res.status} ${res.statusText} ${text || ""}`);
  }

  const json = await res.json();
  if (json.status !== "success") {
    throw new Error(json.error || "Unknown error from backend");
  }

  const data = json.logs || {};
  return {
    columns: Array.isArray(data.columns) ? data.columns : [],
    rows: Array.isArray(data.rows) ? data.rows : [],
    total: typeof data.total === "number" ? data.total : 0,
    limit: typeof data.limit === "number" ? data.limit : limit,
    offset: typeof data.offset === "number" ? data.offset : offset,
  };
}