// frontend/src/components/GetResultsPage/GetResultsCard.jsx
import { useState } from "react";
import ResultsTable from "./ResultsTable";
import ResultsReadyProjectSelect from "./ResultsReadyProjectSelect";
import { useResultsTable } from "../../hooks/GetResultsPage/useResultsTable";
import { useAppContext } from "../../context/AppContext";

export default function GetResultsCard() {
  const { projectName, saveProjectName } = useAppContext();
  const { columns, rows, loading, err, load, reset } = useResultsTable();
  const [submitted, setSubmitted] = useState(false);

  const canSubmit = projectName.trim();

  const onSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    if (canSubmit) load(projectName);
  };

  const onProjectChange = (name) => {
    saveProjectName(name);
    setSubmitted(false);
    reset();
  };

  return (
    <div className="p-8 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
      <h1 className="text-2xl font-semibold mb-4">Get Results</h1>
      <p className="text-xtractyl-outline/70 mb-6">
        Select your project and submit to get your database (prelabelling has to be completed to see
        the results).
      </p>
      <div className="mt-6 border border-xtractyl-outline/20 p-4 flex flex-col gap-4 bg-xtractyl-offwhite">
        <form onSubmit={onSubmit} className="flex flex-row items-end gap-4">
          <ResultsReadyProjectSelect selected={projectName} onChange={onProjectChange} />
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
            {err}
          </div>
        ) : null}

        {submitted ? <ResultsTable columns={columns} rows={rows} /> : null}
      </div>
    </div>
  );
}
