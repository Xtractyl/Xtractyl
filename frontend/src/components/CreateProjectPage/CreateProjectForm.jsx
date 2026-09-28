//src/components/CreateProjectPage/CreateProjectForm.jsx
import useFormState from "../../hooks/CreateProjectPage/useFormState.js";
import useError from "../../hooks/CreateProjectPage/useError.js";
import { splitLines } from "../../utils/CreateProjectPage/splitLines.js";
import ConvertedProjectSelect from "./ConvertedProjectSelect";
import QuestionsLabelsTable from "./QuestionsLabelsTable";

export default function CreateProjectForm({ onCreateProject, busy }) {
  const { title, setTitle, questions, setQuestions, labels, setLabels, resetForm } = useFormState();
  const { error, setError, clearError } = useError();

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    clearError();

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

    const success = await onCreateProject({
      title: title.trim(),
      questions: parsedQuestions,
      labels: parsedLabels,
    });
    if (success) resetForm();
  };

  return (
    <form
      onSubmit={handleFormSubmit}
      className="space-y-6 mt-10 bg-xtractyl-offwhite p-6 rounded shadow w-full"
    >
      <ConvertedProjectSelect selected={title} onChange={setTitle} />

      {/* Numbered Questions + Labels Table */}
      <QuestionsLabelsTable
        questions={questions}
        labels={labels}
        setQuestions={setQuestions}
        setLabels={setLabels}
      />

      {error && <p className="text-sm text-xtractyl-orange">{error}</p>}

      <button
        type="submit"
        disabled={busy}
        className={`px-4 py-2 rounded text-xtractyl-white ${
          busy
            ? "bg-xtractyl-green/50 cursor-not-allowed"
            : "bg-xtractyl-green hover:bg-xtractyl-green/80 transition"
        }`}
      >
        {busy ? "Creating…" : "Create project"}
      </button>
    </form>
  );
}
