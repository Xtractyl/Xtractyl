import useToken from "../../hooks/CreateProjectPage/useToken.js";
import useCreateProject from "../../hooks/CreateProjectPage/useCreateProject.js";
import TokenInput from "./TokenInput";
import CreateProjectForm from "./CreateProjectForm";

export default function ProjectCard({ onTokenSave }) {
  const { token: apiToken, saveToken: handleLocalTokenSave } = useToken(onTokenSave);
  const { checkProjectExists, createProject } = useCreateProject();

  const handleFormSubmit = async (formData) => {
    try {
      const { exists } = await checkProjectExists(formData.title); 
      if (exists) {
        alert("❌ A project with this name already exists.");
        return;
      }
  
      const result = await createProject({ ...formData, token: apiToken });
      console.log("✅ Project created:", result);
      alert("✅ Project successfully created!");
    } catch (error) {
      console.error("❌ Error:", error);
      alert("Something went wrong. See console for details.");
    }
  };

  return (
    
    <div className="p-8 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Create Project</h1>
      <p className="text-gray-600 mb-6">
        Enter API token, choose a project name, enter your questions as well as labels for them.
      </p>
      <TokenInput onTokenSave={handleLocalTokenSave} />
      {apiToken && <CreateProjectForm onSubmit={handleFormSubmit} />}
    </div>
  );
}