import { useState } from "react";
import TokenInput from "../components/TokenInput";
import CreateProjectForm from "../components/CreateProjectForm";

export default function CreateProjectPage() {
  const [apiToken, setApiToken] = useState("");

  const handleFormSubmit = async (formData) => {
    const payload = {
      title: formData.title,
      questions: formData.questions,
      labels: formData.labels,
      token: apiToken,
    };

    try {
      // 🔐 Schritt 1: Projektname prüfen
      const checkResponse = await fetch("http://localhost:5001/project_exists", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title: formData.title }),
      });

      if (!checkResponse.ok) {
        throw new Error("Failed to check if project exists");
      }

      const checkResult = await checkResponse.json();
      if (checkResult.exists) {
        alert("❌ A project with this name already exists. Please choose a different name.");
        return;
      }

      // 📤 Schritt 2: Projekt in Label Studio erstellen + Fragen/Labels speichern
      const response = await fetch("http://localhost:5001/create_project", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const result = await response.json();
      console.log("✅ Project created:", result);
      alert("✅ Project successfully created!");
    } catch (error) {
      console.error("❌ Error:", error);
      alert("Something went wrong. See console for details.");
    }
  };

  return (
    <div className="p-6">
      {/* Intro-Bereich */}
      <div>
        <h1 className="text-2xl font-semibold mb-4">Create Project</h1>
        <p className="text-gray-600">Create your project.</p>
      </div>

      {/* Token holen */}
      <div className="mt-14">
        <a
          href="http://localhost:8080/user/account"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-xtractyl-orange text-white text-base font-medium px-5 py-2 rounded shadow hover:bg-orange-600 transition"
        >
          Get your legacy token
        </a>
        <p className="mt-6 text-sm text-gray-500">
          Return to this tab after copying the token.
        </p>
      </div>

      {/* Token-Eingabe + Formular */}
      <div className="mt-10">
        <TokenInput onTokenSave={setApiToken} />

        {apiToken && (
          <div className="mt-4">
            <p className="text-gray-600">Token saved!</p>
            <CreateProjectForm onSubmit={handleFormSubmit} />
          </div>
        )}
      </div>
    </div>
  );
}