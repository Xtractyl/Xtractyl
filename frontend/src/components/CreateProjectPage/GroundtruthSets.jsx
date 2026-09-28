// src/components/CreateProjectPage/GroundtruthSets.jsx
import { useState } from "react";
import { fetchGroundtruthQuestionsAndLabels } from "../../api/CreateProjectPage/api";

export default function GroundtruthSets() {
  const [groundtruthSets, setGroundtruthSets] = useState([]);
  const [groundtruthError, setGroundtruthError] = useState("");
  const [groundtruthLoading, setGroundtruthLoading] = useState(false);

  const handleLoadGroundtruth = async () => {
    setGroundtruthError("");
    setGroundtruthLoading(true);
    try {
      const data = await fetchGroundtruthQuestionsAndLabels();
      setGroundtruthSets(Object.entries(data).map(([name, qal]) => ({ name, qal })));
    } catch (err) {
      console.error(err);
      setGroundtruthError(err.message || "Failed to load groundtruth questions and labels.");
    } finally {
      setGroundtruthLoading(false);
    }
  };

  return (
    <div className="mt-4 border rounded p-3 bg-xtractyl-offwhite">
      <button
        type="button"
        onClick={handleLoadGroundtruth}
        className="text-sm px-3 py-1.5 rounded bg-xtractyl-offwhite text-xtractyl-outline hover:bg-xtractyl-offwhite disabled:opacity-50"
        disabled={groundtruthLoading}
      >
        {groundtruthLoading
          ? "Loading ground truth…"
          : "Show questions & labels of existing ground truth sets"}
      </button>

      {groundtruthError && <p className="mt-2 text-sm text-xtractyl-orange">{groundtruthError}</p>}

      {groundtruthSets.length > 0 && (
        <div className="mt-4 space-y-4">
          {groundtruthSets.map((set) => (
            <div key={set.name} className="bg-xtractyl-white p-4 rounded max-h-96 overflow-auto">
              <h3 className="font-semibold mb-2">{set.name}</h3>
              <p className="text-xs text-xtractyl-outline/70 mb-2">
                You can click next to a column and drag to select all questions or all labels
                (ctrl+c to copy)
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs font-medium mb-1 text-xtractyl-outline/70">Questions</div>
                  <pre className="text-xs whitespace-pre-wrap break-words">
                    {(set.qal.questions || []).join("\n")}
                  </pre>
                </div>
                <div>
                  <div className="text-xs font-medium mb-1 text-xtractyl-outline/70">Labels</div>
                  <pre className="text-xs whitespace-pre-wrap break-words">
                    {(set.qal.labels || []).join("\n")}
                  </pre>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
