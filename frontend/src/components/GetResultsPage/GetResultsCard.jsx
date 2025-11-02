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
          Submit
        </button>
      </form>

        <div className="flex justify-between items-center mt-4 gap-2">
        <label className="font-medium text-[13px] mb-1 text-gray-700">Limit</label>
        <input
          type="number"
          min={1}
          max={200}
          value={limit}
          onChange={(e) =>
            setLimit(Math.max(1, Math.min(200, Number(e.target.value) || 1)))
          }
          className="border border-gray-300 rounded-md text-sm outline-none px-2.5 py-1.5 w-[100px] focus:ring-2 focus:ring-xtractyl-lightgreen"
        />
          <label className="font-medium text-[13px] mb-1 text-gray-700">Offset</label>
          <input
            type="number"
            min={0}
            value={offset}
            onChange={(e) => setOffset(Math.max(0, Number(e.target.value) || 0))}
            className="border border-gray-300 rounded-md text-sm outline-none px-2.5 py-1.5 w-[100px] focus:ring-2 focus:ring-xtractyl-lightgreen"

          />
         <span className="text-gray-500">
            Page {page} / {pageCount} • Total {total}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setOffset((o) => Math.max(0, o - limit))}
            disabled={offset <= 0 || loading}
            className="px-3 py-2 bg-xtractyl-green text-white rounded-md cursor-pointer hover:bg-xtractyl-lightgreen hover:text-xtractyl-offwhite transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Prev
          </button>

          <button
            type="button"
            onClick={() => setOffset((o) => (o + limit < total ? o + limit : o))}
            disabled={offset + limit >= total || loading}
            className="px-3 py-2 bg-xtractyl-green text-white rounded-md cursor-pointer hover:bg-xtractyl-lightgreen hover:text-xtractyl-offwhite transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
      </div>

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




