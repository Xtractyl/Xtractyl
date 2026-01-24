// frontend/src/components/GetResultsPage/GetResultsCard.jsx
import React, { useCallback, useEffect, useMemo, useState } from "react";
import ResultsTable from "./ResultsTable";
import { getResultsTable } from "../../api/GetResultsPage/api.js";

const LS_BASE = import.meta.env.VITE_LS_BASE || "http://localhost:8080"; // only for links

export default function GetResultsCard({ apiToken, projectName}) {
  const [localProjectName, setLocalProjectName] = useState(projectName || "");
  const [token, setToken] = useState(apiToken || "");
  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const canSubmit = useMemo(
    () => localProjectName.trim() && token.trim(),
    [localProjectName, token]
  );

  useEffect(() => {
    setLocalProjectName(projectName || "");
    setSubmitted(false);
    setColumns([]);
    setRows([]);
  }, [projectName]);

  useEffect(() => {
      setToken(apiToken || "");
      setSubmitted(false);
      setColumns([]);
      setRows([]);
    }, [apiToken]);

  const fetchData = useCallback(async () => {
    if (!canSubmit) return;
    setLoading(true);
    setErr("");
    try {
      const data = await getResultsTable({
        projectName: localProjectName,
        token,
      });
      setColumns(Array.isArray(data.columns) ? data.columns : []);
      setRows(Array.isArray(data.rows) ? data.rows : []);
    } catch (e) {
      setErr(e.message || "Request failed");
      setColumns([]);
      setRows([]);
    } finally {
      setLoading(false);
    }
    }, [canSubmit, localProjectName, token]);

  const onSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    fetchData();
  };

  return (
    <div className="p-8 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
      <h1 className="text-2xl font-semibold mb-4">Get Results</h1>
      <p className="text-gray-600">
        Enter your project name, enter your API token and submit to get your database (re-submit your data to update in case the AI is still running).
      </p>
      <div className="mb-6"></div>
          <a
            href={`${LS_BASE}/user/account/legacy-token`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-xtractyl-orange text-white  text-xtractyl-outline/70ase font-medium px-5 py-2 rounded shadow hover:bg-xtractyl-orange-600 transition"
          >
            Get your legacy token
          </a>
          <p className="mt-2 text-sm text-gray-500">
            Return here after copying the token from Label Studio.
          </p>
          <p className="mt-1 text-sm text-gray-500">
            ⚠️ If you see no legacy token there, go to{" "}
            <a
              href={`${LS_BASE}/organization/`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xtractyl-greenhover:underline"
            >
              {LS_BASE}/organization
            </a>{" "}
            and enable it via the API Tokens settings.
          </p>        
      <div className="mt-6 border border-gray-200 p-4 flex flex-col gap-4 bg-xtractyl-offwhite">
        <form onSubmit={onSubmit} className="flex flex-row items-end gap-4">
          <div className="flex flex-col flex-1">
            <label className="font-semibold mb-2">Project name</label>
            <input
              type="text"
              placeholder="e.g., results"
              value={localProjectName}
              onChange={(e) => setLocalProjectName(e.target.value)}
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
            {loading ? "Loading…" : "Submit & Save as CSV"}
          </button>
        </form>

        {err ? (
          <div className="p-3 border border-red-200 bg-xtractyl-offwhite text-rose-900 rounded-md">
            <strong>Error, does the project already exist in labelstudio?</strong> {err}
          </div>
        ) : null}

         {submitted ? <ResultsTable columns={columns} rows={rows} /> : null}
      </div>
    </div>
  );
}