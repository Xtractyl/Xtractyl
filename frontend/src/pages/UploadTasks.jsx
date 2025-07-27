import React, { useState } from "react";
import ProjectNameInput from "../components/ProjectNameInput";
import HtmlFolderSelect from "../components/HTMLFolderSelect";

export default function UploadTasksPage({ apiToken }) {
  const [projectName, setProjectName] = useState("");
  const [htmlFolder, setHtmlFolder] = useState("");
  const [status, setStatus] = useState(null);

  const handleUpload = async () => {
    if (!projectName || !htmlFolder || !apiToken) {
      alert("Please provide all fields.");
      return;
    }

    try {
      const response = await fetch("http://localhost:5001/upload_tasks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
            project_name: projectName,
            token: apiToken,
            html_folder: htmlFolder
          })
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const result = await response.json();
      console.log("✅ Upload success:", result);
      setStatus("✅ Tasks uploaded successfully.");
    } catch (error) {
      console.error("❌ Upload error:", error);
      setStatus("❌ Upload failed. See console for details.");
    }
  };

  return (
    <div className="p-6 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Upload Tasks</h1>
      <p className="text-gray-600 mb-6">
        Select your project and HTML folder to upload tasks.
      </p>

      <div className="space-y-6 bg-[#ede6d6] p-6 rounded shadow max-w-xl">
        <ProjectNameInput value={projectName} onChange={setProjectName} />
        <HtmlFolderSelect selected={htmlFolder} onChange={setHtmlFolder} />

        <button
          onClick={handleUpload}
          className="bg-[#6baa56] text-white px-4 py-2 rounded hover:bg-[#5b823f]"
        >
          Upload HTML Tasks
        </button>

        {status && <p className="mt-4 text-sm">{status}</p>}
      </div>
    </div>
  );
}