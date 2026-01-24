import useFormState from "../../hooks/CreateProjectPage/useFormState.js";
import useError from "../../hooks/CreateProjectPage/useError.js";
import useSplitLines from "../../hooks/CreateProjectPage/useSplitLines.js";

export default function CreateProjectForm({ onSubmit }) {
  const { title, setTitle, questions, setQuestions, labels, setLabels, resetForm } = useFormState();
  const { error, setError, clearError } = useError();
  const { splitLines } = useSplitLines();

  const handleFormSubmit = (e) => {
    e.preventDefault();
    clearError();

    const parsedQuestions = splitLines(questions);
    const parsedLabels = splitLines(labels);

    if (!title.trim() || parsedQuestions.length === 0 || parsedLabels.length === 0) {
      setError("Please add a project name and at least one question and label.");
      return;
    }

    if (parsedLabels.length !== parsedQuestions.length) {
      setError(`Questions (${parsedQuestions.length}) and labels (${parsedLabels.length}) must have the same count.`);
      return;
    }

    onSubmit({ title: title.trim(), questions: parsedQuestions, labels: parsedLabels });
    resetForm();
  };

  return (
    <form onSubmit={handleFormSubmit} className="space-y-6 mt-10 bg-xtractyl-offwhite p-6 rounded shadow w-full">
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

{/* Numbered Questions + Labels Table */}
{(() => {
  const questionLines = (questions || "").replace(/\r\n/g, "\n").split("\n");
  const labelLines = (labels || "").replace(/\r\n/g, "\n").split("\n");
  const rowCount = Math.max(questionLines.length, labelLines.length, 1);

  const handleQuestionLineChange = (index, value) => {
    const lines = [...questionLines];
    lines[index] = value;

    // Wenn letzte Zeile & nicht leer → neue leere Zeile anhängen
    if (index === lines.length - 1 && value.trim() !== "") {
      lines.push("");
    }

    setQuestions(lines.join("\n"));
  };

  const handleLabelLineChange = (index, value) => {
    const lines = [...labelLines];
    lines[index] = value;

    if (index === lines.length - 1 && value.trim() !== "") {
      lines.push("");
    }

    setLabels(lines.join("\n"));
  };

  return (
    <div className="mt-4 border border-gray-300 rounded-md overflow-hidden">
      {/* Header */}
    <div className="grid grid-cols-[3rem,1fr,1fr] bg-xtractyl-offwhite text-xs font-semibold px-3 py-2 border-b border-gray-300">
      <div>#</div>
      <div className="border-l border-gray-300 border-r pl-2 pr-2">Question</div>
      <div>Label</div>
    </div>

      {/* Rows */}
      <div className="divide-y divide-gray-200">
        {Array.from({ length: rowCount }).map((_, idx) => (
          <div key={idx} className="grid grid-cols-[3rem,1fr,1fr] px-3 py-2 items-center">
            <div className="text-xs  text-xtractyl-outline/60">{idx + 1}</div>

            <input
              type="text"
              value={questionLines[idx] || ""}
              onChange={(e) => handleQuestionLineChange(idx, e.target.value)}
              placeholder={idx === 0 ? "e.g., What is the patient ID?" : ""}
              className="w-full text-sm px-2 py-1 border border-gray-200 rounded-md whitespace-nowrap overflow-x-auto overflow-y-hidden focus:outline-none focus:ring-1 focus:ring-xtractyl-lightgreen"
            />

            <input
              type="text"
              value={labelLines[idx] || ""}
              onChange={(e) => handleLabelLineChange(idx, e.target.value)}
              placeholder={idx === 0 ? "e.g., Patient ID" : ""}
              className="w-full text-sm px-2 py-1 border border-gray-200 rounded-md whitespace-nowrap overflow-x-auto overflow-y-hidden focus:outline-none focus:ring-1 focus:ring-xtractyl-lightgreen"
            />
          </div>
        ))}
      </div>
    </div>
  );
})()}

      {error && <p className="text-sm text-xtractyl-orange">{error}</p>}

      <button type="submit" className="bg-xtractyl-green text-xtractyl-white px-4 py-2 rounded hover:bg-xtractyl-green transition">
        Create project
      </button>
    </form>
  );
}