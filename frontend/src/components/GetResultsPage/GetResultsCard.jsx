// frontend/src/components/GetResultsPage/GetResultsCard.jsx
import React, { useCallback, useEffect, useMemo, useState } from "react";
import ResultsTable from "./ResultsTable";
import { getResultsTable } from "../../api/GetResultsPage/api.js";

export default function GetResultsCard() {
  const [projectName, setProjectName] = useState(() => localStorage.getItem("ls_project_name") || "");
  const [token, setToken] = useState(() => localStorage.getItem("ls_token") || "");

  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);

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
      // Backend liefert jetzt ALLE Daten für das Projekt
      const data = await getResultsTable({ projectName, token });
      setColumns(Array.isArray(data.columns) ? data.columns : []);
      setRows(Array.isArray(data.rows) ? data.rows : []);
    } catch (e) {
      setErr(e.message || "Request failed");
      setColumns([]);
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [canSubmit, projectName, token]);

  const onSubmit = (e) => {
    e.preventDefault();
    fetchData();
  };

  // Optional: automatisch laden, sobald beides vorhanden ist
  useEffect(() => {
    if (canSubmit) fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canSubmit]);

  return (
    <div className="p-8 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Get Results</h1>
      <p className="text-gray-600">
        Enter your project name, enter your API token and submit to get your database (re-submit your data to update in case the AI is still running).
      </p>

      <div className="mt-6 border border-gray-200 p-4 flex flex-col gap-4 bg-xtractyl-offwhite">
        <form onSubmit={onSubmit} className="flex flex-row items-end gap-4">
          <div className="flex flex-col flex-1">
            <label className="font-semibold mb-2">Project name</label>
            <input
              type="text"
              placeholder="e.g., results"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              required
              className="border border-gray-300 rounded-md text-sm px-3 py-2 outline-none w-full focus:ring-2 focus:ring-xtractyl-lightgreen"
            />
          </div>

          <div className="flex flex-col flex-1">
            <label className="font-semibold mb-2">Label Studio Token</label>
            <input
              type="password"
              placeholder="Enter token"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              required
              className="border border-gray-300 rounded-md text-sm px-3 py-2 outline-none w-full focus:ring-2 focus:ring-xtractyl-lightgreen"
            />
          </div>

          <button
            type="submit"
            disabled={!canSubmit || loading}
            className="px-3 py-2 bg-xtractyl-green text-white rounded-md cursor-pointer hover:bg-xtractyl-lightgreen hover:text-xtractyl-offwhite "
          >
            {loading ? "Loading…" : "Submit"}
          </button>
        </form>

        {err ? (
          <div className="p-3 border border-red-200 bg-rose-50 text-rose-900 rounded-md">
            <strong>Error:</strong> {err}
          </div>
        ) : null}

        <ResultsTable columns={columns} rows={rows} />
      </div>
    </div>
  );
}