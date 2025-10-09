// frontend/src/components/GetResultsPage/ResultsTable.jsx
import React from "react";

export default function ResultsTable({ columns, rows }) {
  if (!columns?.length) return <div className="muted">No columns.</div>;
  if (!rows?.length) return <div className="muted">No data.</div>;

  return (
    <div style={{ overflowX: "auto", border: "1px solid #e5e7eb", borderRadius: 8 }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
        <thead style={{ position: "sticky", top: 0, background: "#fafafa", zIndex: 1 }}>
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                style={{
                  textAlign: "left",
                  padding: "10px 12px",
                  borderBottom: "1px solid #e5e7eb",
                  whiteSpace: "nowrap",
                }}
                title={col}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ridx) => (
            <tr key={ridx} style={{ borderBottom: "1px solid #f1f5f9" }}>
              {columns.map((col) => (
                <td key={col} style={{ padding: "8px 12px", verticalAlign: "top" }}>
                  {formatCell(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(value) {
  if (value == null) return "";
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
  return String(value);
}