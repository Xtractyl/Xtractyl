// src/components/CreateProjectPage/CreateProjectCard.jsx
import { useState } from "react";
import useCreateProject from "../../hooks/CreateProjectPage/useCreateProject.js";
import TokenInput from "./TokenInput";
import CreateProjectForm from "./CreateProjectForm";
import { fetchGroundtruthQuestionsAndLabels } from "../../api/CreateProjectPage/api";
import { useAppContext } from "../../context/AppContext";

export default function CreateProjectCard() {
  const { checkProjectExists, createProject } = useCreateProject();
  const [groundtruthSets, setGroundtruthSets] = useState([]);
  const [groundtruthError, setGroundtruthError] = useState("");
  const [groundtruthLoading, setGroundtruthLoading] = useState(false);
  const { token, projectName, saveProjectName } = useAppContext();

  const handleFormSubmit = async (formData) => {
    try {
      if (!token) {
        alert("Please enter and save an API token first.");
        return;
      }
      await checkProjectExists(formData.title);


      saveProjectName(formData.title);

      const result = await createProject({
        ...formData,
        token: token, 
      });

      console.log("✅ Project created");
      alert("✅ Project successfully created!");
    } catch (error) {
      console.error("❌ Error");
      if (error.message === "PROJECT_ALREADY_EXISTS") {
        alert("❌ A project with this name already exists.");
      } else {
        alert("Something went wrong.");
     }
    }
  };

    const handleLoadGroundtruth = async () => {
    setGroundtruthError("");
    setGroundtruthLoading(true);
    try {
      const data = await fetchGroundtruthQuestionsAndLabels();
      setGroundtruthSets(Object.entries(data).map(([name, qal]) => ({ name, qal })));
    } catch (err) {
      console.error(err);
      setGroundtruthError("Failed to load groundtruth questions and labels.");
    } finally {
      setGroundtruthLoading(false);
    }
  };

  return (
    <div className="p-8 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
      <h1 className="text-2xl font-semibold mb-4">Create Project</h1>
      <p className="text-xtractyl-outline/70 mb-6">
        Enter API token, choose a project name, enter your questions as well as labels for them.
      </p>

      {/* TokenInput sagt nur nach oben Bescheid */}
      <TokenInput />

      {/* Formular nur, wenn App schon einen Token kennt */}
      {token && <CreateProjectForm onSubmit={handleFormSubmit} />}

          {/* Groundtruth helper section */}
      <div className="mt-4 border rounded p-3 bg-xtractyl-offwhite">
        <h2 className="text-xtractyl-outline/70ase font-medium mb-1 text-xtractyl-outline">
          Use questions & labels from ground truth projects set up for time series
        </h2>
        <p className="text-xs  text-xtractyl-outline/60 mb-1">
          Click the button to show the questions and labels for ground truth sets set up for time series
        </p>

        <button
          type="button"
          onClick={handleLoadGroundtruth}
          className="text-sm px-3 py-1.5 rounded bg-xtractyl-offwhite text-xtractyl-outline hover:bg-xtractyl-offwhite disabled:opacity-50"
          disabled={groundtruthLoading}
        >
          {groundtruthLoading
            ? "Loading ground truth…"
            : "Show ground truth questions & labels"}
        </button>

        {groundtruthError && (
          <p className="mt-2 text-sm text-xtractyl-orange">{groundtruthError}</p>
        )}

       {groundtruthSets.length > 0 && (
         <div className="mt-4 space-y-4">
            {groundtruthSets.map((set) => (
              <div key={set.name} className="bg-xtractyl-white p-4 rounded max-h-96 overflow-auto">
                <h3 className="font-semibold mb-2">{set.name}</h3>
                <p className="text-xs text-xtractyl-outline/70 mb-2">
                  Copy relevant questions and labels into your own project configuration.
                </p>
                <pre className="text-xs whitespace-pre-wrap break-words">
                  {JSON.stringify(set.qal, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div> 
    </div>
  );
}