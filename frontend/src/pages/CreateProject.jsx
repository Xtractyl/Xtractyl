// src/pages/CreateProject.jsx
import CreateProjectCard from "../components/CreateProjectPage/CreateProjectCard";

export default function CreateProjectPage({ apiToken, onTokenSave, projectName,  onProjectNameSave }) {
  return (
    <CreateProjectCard
      apiToken={apiToken}
      onTokenSave={onTokenSave}
      projectName={projectName}
      onProjectNameSave={onProjectNameSave}
    />
  );
}