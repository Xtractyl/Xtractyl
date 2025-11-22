// src/pages/StartPrelabelling.jsx
import StartPrelabellingCard from "../components/StartPrelabellingPage/StartPrelabellingCard";

export default function StartPrelabellingPage({ apiToken, projectName }) {
  return <StartPrelabellingCard 
    apiToken={apiToken}
    projectName={projectName}
  />
  ;
}

