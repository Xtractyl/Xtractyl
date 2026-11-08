// frontend/src/hooks/EvaluationDriftPage/useEvaluatedProjects.js
import { useEffect, useState } from "react";
import { fetchEvaluatedProjects } from "../../api/EvaluationDriftPage/api.js";

export function useEvaluatedProjects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    async function run() {
      try {
        setErrorMsg("");
        const names = await fetchEvaluatedProjects();
        setProjects(names);
      } catch (e) {
        setErrorMsg(e?.message || "Failed to load evaluated projects");
      } finally {
        setLoading(false);
      }
    }
    run();
  }, []);

  return { projects, loading, errorMsg };
}
