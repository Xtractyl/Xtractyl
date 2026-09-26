//src/components/CreateProjectPage/CreateProjectForm.jsx
import useFormState from "../../hooks/CreateProjectPage/useFormState.js";
import useError from "../../hooks/CreateProjectPage/useError.js";
import useSplitLines from "../../hooks/CreateProjectPage/useSplitLines.js";
import ConvertedProjectSelect from "./ConvertedProjectSelect";
import QuestionsLabelsTable from "./QuestionsLabelsTable";

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
      <ConvertedProjectSelect selected={title} onChange={setTitle} />

      {/* Numbered Questions + Labels Table */}
      <QuestionsLabelsTable
        questions={questions}
        labels={labels}
        setQuestions={setQuestions}
        setLabels={setLabels}
      />

      {error && <p className="text-sm text-xtractyl-orange">{error}</p>}

      <button type="submit" className="bg-xtractyl-green text-xtractyl-white px-4 py-2 rounded hover:bg-xtractyl-green/80 transition">
        Create project
      </button>
    </form>
  );
}
