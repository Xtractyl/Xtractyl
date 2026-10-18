// frontend/src/hooks/GetResultsPage/useResultsTable.js
import { useState } from "react";
import { getResultsTable } from "../../api/GetResultsPage/api.js";

export function useResultsTable() {
  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const reset = () => {
    setColumns([]);
    setRows([]);
    setErr("");
  };

  const load = async (projectName) => {
    setLoading(true);
    setErr("");
    try {
      const data = await getResultsTable({ projectName });
      setColumns(data.columns);
      setRows(data.rows);
    } catch (e) {
      setErr(e.message || "Request failed");
      setColumns([]);
      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  return { columns, rows, loading, err, load, reset };
}
