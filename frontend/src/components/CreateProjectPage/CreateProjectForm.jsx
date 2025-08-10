import { useState } from "react";

export default function CreateProjectForm({ onSubmit }) {
  const [title, setTitle] = useState("");
  const [questions, setQuestions] = useState("");
  const [labels, setLabels] = useState("");
  const [error, setError] = useState("");

  const splitLines = (v) =>
    v
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);

  const handleFormSubmit = (e) => {
    e.preventDefault();
    setError("");

    const parsedQuestions = splitLines(questions);
    const parsedLabels = splitLines(labels);

    if (!title.trim() || parsedQuestions.length === 0 || parsedLabels.length === 0) {
      setError("Please add a project name and at least one question and label.");
      return;
    }

    if (parsedLabels.length !== parsedQuestions.length) {
      setError(
        `Questions (${parsedQuestions.length}) and labels (${parsedLabels.length}) must have the same count.`
      );
      return;
    }

    // Pass everything to the parent component
    onSubmit({
      title: title.trim(),
      questions: parsedQuestions,
      labels: parsedLabels,
    });

    // Optional reset
    setTitle("");
    setQuestions("");
    setLabels("");
  };

  return (
    <form onSubmit={handleFormSubmit} className="space-y-6 mt-10 bg-beige p-6 rounded shadow w-full">
      <div>
        <label className="block text-sm font-medium mb-1">Project name</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="At least 3 characters. Use letters, numbers, underscores. Example: Oncology_June_2025"
          className="w-full px-3 py-2 border rounded"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Questions (one per line)</label>
        <textarea
          value={questions}
          onChange={(e) => setQuestions(e.target.value)}
          rows={5}
          placeholder="e.g., What is the patient ID?"
          className="w-full px-3 py-2 border rounded"
        />
        <p className="mt-1 text-xs text-gray-600">
          {splitLines(questions).length} question(s)
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Labels (one per question)</label>
        <textarea
          value={labels}
          onChange={(e) => setLabels(e.target.value)}
          rows={4}
          placeholder="e.g., Patient ID"
          className="w-full px-3 py-2 border rounded"
        />
        <p className="mt-1 text-xs text-gray-600">
          {splitLines(labels).length} label(s)
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        className="bg-xtractyl-green text-white px-4 py-2 rounded hover:bg-green-700 transition"
      >
        Create project
      </button>
    </form>
  );
}