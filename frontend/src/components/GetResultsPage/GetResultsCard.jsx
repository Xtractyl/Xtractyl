// frontend/src/components/GetResultsPage/GetResultsCard.jsx
import { useState } from "react";
import ResultsTable from "./ResultsTable";
import ResultsReadyProjectSelect from "./ResultsReadyProjectSelect";
import { getResultsTable } from "../../api/GetResultsPage/api.js";
import { useAppContext } from "../../context/AppContext";

export default function GetResultsCard() {
  const { projectName, saveProjectName } = useAppContext();
  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const canSubmit = projectName.trim();


  const fetchData = async () => {
    if (!canSubmit) return;
    setLoading(true);
    setErr("");
    try {
      const data = await getResultsTable({
        projectName,
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
        Select your project and submit to get your database (prelabelling has to be completed to see the results).
      </p>
      <div className="mb-6"></div>
      <div className="mt-6 border border-xtractyl-outline/20 p-4 flex flex-col gap-4 bg-xtractyl-offwhite">
      <form onSubmit={onSubmit} className="flex flex-row items-end gap-4">
        <ResultsReadyProjectSelect
          selected={projectName}
          onChange={saveProjectName}
        />

        <button
          type="submit"
          disabled={!canSubmit || loading}
          className="px-3 py-2 bg-xtractyl-green text-xtractyl-white rounded-md cursor-pointer hover:bg-xtractyl-green/80"
        >
          {loading ? "Loading…" : "Submit"}
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