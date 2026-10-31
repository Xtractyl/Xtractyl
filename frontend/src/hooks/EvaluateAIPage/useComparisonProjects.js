// frontend/src/hooks/EvaluateAIPage/useComparisonProjects.js
import { useEffect, useState } from "react";
import { getProjectsReadyForComparison } from "../../api/EvaluateAIPage/api.js";

export function useComparisonProjects(reloadKey) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [comparisonProject, setComparisonProject] = useState("");

  useEffect(() => {
    setLoading(true);
    setErrorMsg("");
    getProjectsReadyForComparison()
      .then((projectList) => {
        setProjects(projectList);
        if (projectList.length > 0) {
          setComparisonProject((prev) => (projectList.includes(prev) ? prev : projectList[0]));
        } else {
          setComparisonProject("");
        }
      })
      .catch((e) => {
        setErrorMsg(e.message || "Failed to load projects.");
        setComparisonProject("");
      })
      .finally(() => setLoading(false));
  }, [reloadKey]);

  return { projects, loading, errorMsg, comparisonProject, setComparisonProject };
}
