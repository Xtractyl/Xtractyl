// src/pages/GetResults.jsx
import GetResultsCard from "../components/GetResultsPage/GetResultsCard";

export default function GetResultsPage({ apiToken, projectName }) {
  return <GetResultsCard 
      apiToken={apiToken} 
      projectName={projectName}
  />
  ;
}


