// src/pages/CreateProject.jsx
import CreateProjectCard from "../components/CreateProjectPage/CreateProjectCard";

export default function CreateProjectPage({ apiToken, onTokenSave }) {
  return (
    <CreateProjectCard
      apiToken={apiToken}
      onTokenSave={onTokenSave}
    />
  );
}