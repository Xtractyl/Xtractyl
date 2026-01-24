// frontend/src/api/getResultsTable.js
export async function getResultsTable({ projectName, token }) {
  const baseUrl = import.meta.env.VITE_ORCH_URL || "http://localhost:5001";
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
    const text = await res.text().catch(() => "");
    throw new Error(`Request failed: ${res.status} ${res.statusText} ${text || ""}`);
  }

  const json = await res.json();
  const data = json?.data ?? json?.logs ?? json ?? {};

  return {
    columns: Array.isArray(data.columns) ? data.columns : [],
    rows: Array.isArray(data.rows) ? data.rows : [],
    total: typeof data.total === "number" ? data.total : 0,
  };
}