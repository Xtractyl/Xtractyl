import React from "react";

export default function ResultsTable({ columns, rows }) {
  if (!columns?.length) return <div className="muted">No columns.</div>;
  if (!rows?.length) return <div className="muted">No data.</div>;

  return (
    <div className="p-8 xtractyl-offwhite min-h-screen text-xtractyl-darktext">

      {/* Horizontal scroll wrapper */}
      <div className="overflow-x-auto border rounded-lg bg-xtractyl-white shadow-sm">

        <table className="border-collapse text-sm whitespace-nowrap min-w-max w-full">
          <thead className="sticky top-0 bg-xtractyl-offwhite z-10">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  style={{
                    textAlign: "left",
                    padding: "10px 12px",
                    borderBottom: "1px solid #e5e7eb",
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
              <tr key={ridx} className="border-b bg-xtractyl-white border-slate-100">
                {columns.map((col) => (
                  <td key={col} className="px-3 py-2 align-top">
                    {formatCell(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>

      </div>
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