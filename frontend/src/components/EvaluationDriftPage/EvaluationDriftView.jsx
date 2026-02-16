// frontend/src/components/EvaluationDriftPage/EvaluationDriftView.jsx
import { useEffect, useState } from "react";
import { fetchEvaluationDrift } from "../../api/EvaluationDriftPage/api.js";

export default function EvaluationDriftView() {
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [items, setItems] = useState([]);

  useEffect(() => {
    async function run() {
      try {
        setLoading(true);
        setErrorMsg("");
        const data = await fetchEvaluationDrift();
        setItems(Array.isArray(data) ? data : []);
      } catch (e) {
        setErrorMsg(e?.message || "Failed to load drift data");
      } finally {
        setLoading(false);
      }
    }
    run();
  }, []);

  if (loading) return <div className="text-sm text-xtractyl-outline/70">Loading…</div>;
  if (errorMsg) return <div className="text-sm text-xtractyl-orange">{errorMsg}</div>;
  if (!items.length)
    return (
      <div className="text-sm text-xtractyl-outline/70">
        No drift data available yet.
      </div>
    );

  return (
    <div className="mt-4 text-sm">
      Loaded <b>{items.length}</b> evaluation runs.
    </div>
  );
}