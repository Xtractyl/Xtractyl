// src/components/CreateProjectPage/CreateProjectCard.jsx
import { useState } from "react";
import useCreateProject from "../../hooks/CreateProjectPage/useCreateProject.js";
import TokenInput from "../shared/TokenInput";
import CreateProjectForm from "./CreateProjectForm";
import GroundtruthSets from "./GroundtruthSets";
import { useAppContext } from "../../context/AppContext";

export default function CreateProjectCard() {
  const { createProject } = useCreateProject();
  const { token, saveProjectName } = useAppContext();
  const [statusMsg, setStatusMsg] = useState("");

  const handleFormSubmit = async (formData) => {
    try {
      if (!token) {
        setStatusMsg("Please enter and save an API token first.");
        return;
      }

      saveProjectName(formData.title);

      await createProject({
        ...formData,
        token,
      });
      setStatusMsg("Project created successfully.");
    } catch (error) {
      setStatusMsg(`${error.message || "Something went wrong."}`);
    }
  };

  return (
    <div className="p-6 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
      <h1 className="text-2xl font-semibold mb-4">Create Project</h1>
      <p className="text-xtractyl-outline/70 mb-6">
        Enter API token, choose a project name, enter your questions as well as labels for them.
      </p>

      <TokenInput />

      {token && (
        <div>
          <CreateProjectForm onSubmit={handleFormSubmit} />
          {statusMsg && <div className="text-sm mt-2">{statusMsg}</div>}
        </div>
      )}

      <GroundtruthSets />
    </div>
  );
}
