// frontend/src/components/GetResultsPage/GetResultsCard.jsx
import React, { useCallback, useEffect, useMemo, useState } from "react";
import ResultsTable from "./ResultsTable";
import { getResultsTable } from "../../api/GetResultsPage/api.js";

export default function GetResultsCard() {
  const [projectName, setProjectName] = useState(() => localStorage.getItem("ls_project_name") || "");
  const [token, setToken] = useState(() => localStorage.getItem("ls_token") || "");
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);

  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const canSubmit = useMemo(() => projectName.trim() && token.trim(), [projectName, token]);

  useEffect(() => {
    localStorage.setItem("ls_project_name", projectName);
  }, [projectName]);

  useEffect(() => {
    localStorage.setItem("ls_token", token);
  }, [token]);

  const fetchData = useCallback(async () => {
    if (!canSubmit) return;
    setLoading(true);
    setErr("");
    try {
      const data = await getResultsTable({ projectName, token, limit, offset });
      setColumns(data.columns);
      setRows(data.rows);
      setTotal(data.total);
    } catch (e) {
      setErr(e.message || "Request failed");
      setColumns([]);
      setRows([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [canSubmit, projectName, token, limit, offset]);

  const onSubmit = (e) => {
    e.preventDefault();
    setOffset(0); // reset pagination on new submit
    // fetch after state commit
    setTimeout(fetchData, 0);
  };

  // optional: auto-fetch when pagination changes and inputs are valid
  useEffect(() => {
    if (canSubmit) fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [limit, offset]);

  const page = Math.floor(offset / Math.max(1, limit)) + 1;
  const pageCount = Math.max(1, Math.ceil(total / Math.max(1, limit)));

  return (
    <div className="p-8 bg-[#e6e2cf] min-h-screen text-[#23211c]">

    <div style={cardStyle}>
      <h2 style={{ margin: 0, fontSize: 20 }}>Results</h2>
      <p style={{ marginTop: 6, color: "#6b7280" }}>
        Enter project name and Label Studio token to fetch the tabular predictions.
      </p>

      <form onSubmit={onSubmit} style={formRow}>
        <div style={fieldCol}>
          <label style={labelStyle}>Project name</label>
          <input
            type="text"
            placeholder="e.g., results"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            style={inputStyle}
            required
          />
        </div>

        <div style={fieldCol}>
          <label style={labelStyle}>Label Studio token</label>
          <input
            type="password"
            placeholder="Enter token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            style={inputStyle}
            required
          />
        </div>

        <div style={{ display: "flex", alignItems: "flex-end", gap: 8 }}>
          <button type="submit" disabled={!canSubmit || loading} style={buttonStyle}>
            {loading ? "Loading…" : "Fetch"}
          </button>
        </div>
      </form>

      <div style={controlsRow}>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label style={labelStyleSm}>Limit</label>
          <input
            type="number"
            min={1}
            max={200}
            value={limit}
            onChange={(e) => setLimit(Math.max(1, Math.min(200, Number(e.target.value) || 1)))}
            style={{ ...inputStyle, width: 100, padding: "6px 10px" }}
          />
          <label style={labelStyleSm}>Offset</label>
          <input
            type="number"
            min={0}
            value={offset}
            onChange={(e) => setOffset(Math.max(0, Number(e.target.value) || 0))}
            style={{ ...inputStyle, width: 120, padding: "6px 10px" }}
          />
          <span style={{ color: "#6b7280" }}>
            Page {page} / {pageCount} • Total {total}
          </span>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button
            type="button"
            onClick={() => setOffset((o) => Math.max(0, o - limit))}
            disabled={offset <= 0 || loading}
            style={buttonGhost}
          >
            Prev
          </button>
          <button
            type="button"
            onClick={() => setOffset((o) => (o + limit < total ? o + limit : o))}
            disabled={offset + limit >= total || loading}
            style={buttonGhost}
          >
            Next
          </button>
        </div>
      </div>

      {err ? (
        <div style={errorBox}>
          <strong>Error:</strong> {err}
        </div>
      ) : null}

      <ResultsTable columns={columns} rows={rows} />
    </div>
    </div>
  );
}

const cardStyle = {
  border: "1px solid #e5e7eb",
  borderRadius: 12,
  padding: 16,
  display: "flex",
  flexDirection: "column",
  gap: 16,
  background: "white",
};

const formRow = {
  display: "grid",
  gridTemplateColumns: "minmax(220px, 1fr) minmax(260px, 1fr) auto",
  gap: 12,
  alignItems: "flex-end",
};

const controlsRow = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
};

const fieldCol = { display: "flex", flexDirection: "column", gap: 6 };

const labelStyle = { fontSize: 12, color: "#374151" };
const labelStyleSm = { fontSize: 12, color: "#6b7280" };

const inputStyle = {
  border: "1px solid #d1d5db",
  borderRadius: 8,
  padding: "8px 12px",
  outline: "none",
  fontSize: 14,
};

const buttonStyle = {
  background: "#111827",
  color: "white",
  border: "1px solid #111827",
  borderRadius: 8,
  padding: "10px 14px",
  cursor: "pointer",
};

const buttonGhost = {
  background: "white",
  color: "#111827",
  border: "1px solid #d1d5db",
  borderRadius: 8,
  padding: "8px 12px",
  cursor: "pointer",
};

const errorBox = {
  padding: 12,
  border: "1px solid #fecaca",
  background: "#fff1f2",
  color: "#7f1d1d",
  borderRadius: 8,
};