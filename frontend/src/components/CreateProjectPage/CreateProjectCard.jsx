// src/components/CreateProjectPage/CreateProjectCard.jsx
import { useState } from "react";
import useCreateProject from "../../hooks/CreateProjectPage/useCreateProject.js";
import TokenInput from "./TokenInput";
import CreateProjectForm from "./CreateProjectForm";
import { fetchGroundtruthQuestionsAndLabels } from "../../api/CreateProjectPage/api";

export default function CreateProjectCard({ apiToken, onTokenSave , onProjectNameSave }) {
  const { checkProjectExists, createProject } = useCreateProject();
  const [groundtruth, setGroundtruth] = useState(null);
  const [groundtruthError, setGroundtruthError] = useState("");
  const [groundtruthLoading, setGroundtruthLoading] = useState(false);

  const handleFormSubmit = async (formData) => {
    try {
      if (!apiToken) {
        alert("Please enter and save an API token first.");
        return;
      }

      const { exists } = await checkProjectExists(formData.title);
      if (exists) {
        alert("❌ A project with this name already exists.");
        return;
      }

    if (onProjectNameSave) {
      onProjectNameSave(formData.title);
    }

      const result = await createProject({
        ...formData,
        token: apiToken, // direkt aus App-Prop
      });

      console.log("✅ Project created:", result);
      alert("✅ Project successfully created!");
    } catch (error) {
      console.error("❌ Error:", error);
      alert("Something went wrong. See console for details.");
    }
  };

    const handleLoadGroundtruth = async () => {
    setGroundtruthError("");
    setGroundtruthLoading(true);
    try {
      const data = await fetchGroundtruthQuestionsAndLabels();
      setGroundtruth(data);
    } catch (err) {
      console.error(err);
      setGroundtruthError("Failed to load groundtruth questions and labels.");
    } finally {
      setGroundtruthLoading(false);
    }
  };

  return (
    <div className="p-8 bg-xtractyl-background min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Create Project</h1>
      <p className="text-gray-600 mb-6">
        Enter API token, choose a project name, enter your questions as well as labels for them.
      </p>

      {/* TokenInput sagt nur nach oben Bescheid */}
      <TokenInput onTokenSave={onTokenSave} />

      {/* Formular nur, wenn App schon einen Token kennt */}
      {apiToken && <CreateProjectForm onSubmit={handleFormSubmit} />}

          {/* Groundtruth helper section */}
      <div className="mt-4 border rounded p-3 bg-xtractyl-offwhite">
        <h2 className="text-base font-medium mb-1 text-gray-700">
          Use questions & labels from standard groundtruth project
        </h2>
        <p className="text-xs text-gray-500 mb-1">
          Click the button to show the questions and labels from the
          Evaluation_Set_Do_Not_Delete project.
        </p>

        <button
          type="button"
          onClick={handleLoadGroundtruth}
          className="text-sm px-3 py-1.5 rounded bg-xtractyl-offwhite text-gray-700 hover:bg-xtractyl-offwhite disabled:opacity-50"
          disabled={groundtruthLoading}
        >
          {groundtruthLoading
            ? "Loading groundtruth…"
            : "Show groundtruth questions & labels"}
        </button>

        {groundtruthError && (
          <p className="mt-2 text-sm text-red-600">{groundtruthError}</p>
        )}

        {groundtruth && (
          <div className="mt-4 bg-xtractyl-offwhite p-4 rounded max-h-96 overflow-auto">
            <h3 className="font-semibold mb-2">
              Groundtruth questions_and_labels.json
            </h3>
            <p className="text-xs text-gray-600 mb-2">
              Copy relevant questions and labels into your own project
              configuration.
            </p>
            <pre className="text-xs whitespace-pre-wrap break-words">
              {JSON.stringify(groundtruth, null, 2)}
            </pre>
          </div>
        )}
      </div> 
    </div>
  );
}