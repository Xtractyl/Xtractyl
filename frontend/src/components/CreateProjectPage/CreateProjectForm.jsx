//src/components/CreateProjectPage/CreateProjectForm.jsx
import { useState } from "react";
import useFormState from "../../hooks/CreateProjectPage/useFormState.js";
import useError from "../../hooks/CreateProjectPage/useError.js";
import { splitLines } from "../../utils/CreateProjectPage/splitLines.js";
import ConvertedProjectSelect from "./ConvertedProjectSelect.jsx";
import QuestionsLabelsTable from "./QuestionsLabelsTable.jsx";
import ProjectLinksReview from "./ProjectLinksReview.jsx";

export default function CreateProjectForm({
  onCheckLinks,
  onCreateProject,
  onDiscardProject,
  busy,
}) {
  const { title, setTitle, questions, setQuestions, labels, setLabels, resetForm } = useFormState();
  const { error, setError, clearError } = useError();
  const [review, setReview] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  const finish = () => {
    resetForm();
    setReview(null);
    setReloadKey((k) => k + 1);
  };

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

    const data = { title: title.trim(), questions: parsedQuestions, labels: parsedLabels };
    const links = await onCheckLinks(data);
    if (links) setReview({ data, links });
  };

  const handleConfirm = async () => {
    if (await onCreateProject(review.data)) finish();
  };

  const handleCancel = async () => {
    if (await onDiscardProject(review.data.title)) finish();
  };

  return (
    <form
      onSubmit={handleFormSubmit}
      className="space-y-6 mt-10 bg-xtractyl-offwhite p-6 rounded shadow w-full"
    >
      {/* Locked while the links are shown, so the reviewed values cannot change */}
      <fieldset disabled={review !== null} className="space-y-6">
        <ConvertedProjectSelect selected={title} onChange={setTitle} reloadKey={reloadKey} />

        {/* Numbered Questions + Labels Table */}
        <QuestionsLabelsTable
          questions={questions}
          labels={labels}
          setQuestions={setQuestions}
          setLabels={setLabels}
        />
      </fieldset>

      {error && <p className="text-sm text-xtractyl-orange">{error}</p>}

      {review ? (
        <ProjectLinksReview
          links={review.links}
          busy={busy}
          onConfirm={handleConfirm}
          onEdit={() => setReview(null)}
          onCancel={handleCancel}
        />
      ) : (
        <button
          type="submit"
          disabled={busy}
          className={`px-4 py-2 rounded text-xtractyl-white ${
            busy
              ? "bg-xtractyl-green/50 cursor-not-allowed"
              : "bg-xtractyl-green hover:bg-xtractyl-green/80 transition"
          }`}
        >
          {busy ? "Checking…" : "Create project"}
        </button>
      )}
    </form>
  );
}
