import { useState } from "react";

export default function CreateProjectForm({ onSubmit }) {
  const [title, setTitle] = useState("");
  const [questions, setQuestions] = useState("");
  const [labels, setLabels] = useState("");

  const handleFormSubmit = (e) => {
    e.preventDefault();

    const parsedQuestions = questions
      .split("\n")
      .map((q) => q.trim())
      .filter((q) => q.length > 0);

    const parsedLabels = labels
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    if (!title || parsedQuestions.length === 0 || parsedLabels.length === 0) {
      alert("Please add a project name and at least one question and label.");
      return;
    }

    // ✅ Übergibt alles an die Parent-Komponente
    onSubmit({
      title: title.trim(),
      questions: parsedQuestions,
      labels: parsedLabels,
    });

    // Optional: Reset
    setTitle("");
    setQuestions("");
    setLabels("");
  };

  return (
    <form onSubmit={handleFormSubmit} className="space-y-6 mt-10 bg-beige p-6 rounded shadow">
      <div>
        <label className="block text-sm font-medium mb-1">Project name:</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="At least 3 characters! Do not use special characters or spaces! Proper example: Oncology_June_2025"
          className="w-full px-3 py-2 border rounded"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Questions (One per line):</label>
        <textarea
          value={questions}
          onChange={(e) => setQuestions(e.target.value)}
          rows={5}
          placeholder="e.g. What is the patient ID?"
          className="w-full px-3 py-2 border rounded"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Labels (One per question):</label>
        <textarea
          value={labels}
          onChange={(e) => setLabels(e.target.value)}
          rows={4}
          placeholder="e.g. Patient ID"
          className="w-full px-3 py-2 border rounded"
        />
      </div>

      <button
        type="submit"
        className="bg-xtractyl-green text-white px-4 py-2 rounded hover:bg-green-700 transition"
      >
        Create project
      </button>
    </form>
  );
}