// frontend/src/components/GetResultsPage/GetResultsCard.jsx
import { useState } from "react";
import ResultsTable from "./ResultsTable";
import { getResultsTable } from "../../api/GetResultsPage/api.js";
import { useAppContext } from "../../context/AppContext";
import TokenLink from "../shared/TokenLink";

export default function GetResultsCard() {
  const { token, projectName, saveToken, saveProjectName } = useAppContext();
  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const canSubmit = projectName.trim() && token.trim();


  const fetchData = async () => {
    if (!canSubmit) return;
    setLoading(true);
    setErr("");
    try {
      const data = await getResultsTable({
        projectName,
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
    };

  const onSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    fetchData();
  };

  return (
    <div className="p-8 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
      <h1 className="text-2xl font-semibold mb-4">Get Results</h1>
      <p className="text-xtractyl-outline/70">
        Enter your project name, enter your API token and submit to get your database (re-submit your data to update in case the AI is still running).
      </p>
      <div className="mb-6"></div>
      < TokenLink />    
      <div className="mt-6 border border-xtractyl-outline/20 p-4 flex flex-col gap-4 bg-xtractyl-offwhite">
        <form onSubmit={onSubmit} className="flex flex-row items-end gap-4">
          <div className="flex flex-col flex-1">
            <label className="font-semibold mb-2">Project name</label>
            <input
              type="text"
              placeholder="e.g., results"
              value={projectName}
              onChange={(e) => saveProjectName(e.target.value)}
              required
              className="border border-xtractyl-outline/30 rounded-md text-sm px-3 py-2 outline-none w-full focus:ring-2 focus:ring-xtractyl-lightgreen"
            />
          </div>

          <div className="flex flex-col flex-1">
            <label className="font-semibold mb-2">Label Studio Token</label>
            <input
              type="password"
              placeholder="Enter token"
              value={token}
              onChange={(e) => saveToken(e.target.value)}
              required
              className="border border-xtractyl-outline/30 rounded-md text-sm px-3 py-2 outline-none w-full focus:ring-2 focus:ring-xtractyl-lightgreen"
            />
          </div>

          <button
            type="submit"
            disabled={!canSubmit || loading}
            className="px-3 py-2 bg-xtractyl-green text-xtractyl-white rounded-md cursor-pointer hover:bg-xtractyl-green/80"
          >
            {loading ? "Loading…" : "Submit & Save as CSV"}
          </button>
        </form>

        {err ? (
       <div className="p-3 border border-xtractyl-orange/30 bg-xtractyl-offwhite text-xtractyl-darktext rounded-md">
        ❌ {err}
      </div>
        ) : null}

         {submitted ? <ResultsTable columns={columns} rows={rows} /> : null}
      </div>
    </div>
  );
}