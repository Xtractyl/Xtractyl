// src/pages/EvaluateAI.jsx
import EvaluateAICard from "../components/EvaluateAIPage/EvaluateAICard";

export default function EvaluateAIPage({ apiToken, projectName }) {
  return <EvaluateAICard 
          apiToken={apiToken}
          projectName={projectName}
          />;
}


