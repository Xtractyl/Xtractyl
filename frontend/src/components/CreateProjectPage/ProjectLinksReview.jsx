// src/components/CreateProjectPage/ProjectLinksReview.jsx
const SECTIONS = [
  {
    key: "comparison",
    title: "Comparison",
    description: "Same labels and same documents.",
  },
  {
    key: "regression",
    title: "Regression",
    description:
      "Same labels, questions and documents. Becomes a regression series if you later use the same model and system prompt.",
  },
  {
    key: "drift",
    title: "Drift",
    description:
      "Same labels and questions, but no document in common. Becomes a drift series if you later use the same model and system prompt.",
  },
];

export default function ProjectLinksReview({ links, busy, onConfirm, onEdit, onCancel }) {
  return (
    <div className="space-y-4 border rounded p-4 bg-xtractyl-background">
      <p className="text-sm">
        Once created, this project is automatically grouped with these existing projects:
      </p>

      {SECTIONS.map(({ key, title, description }) => (
        <section key={key} aria-label={title}>
          <h3 className="font-medium">{title}</h3>
          <p className="text-xs text-xtractyl-outline/70 mb-1">{description}</p>
          {links[key].length === 0 ? (
            <p className="text-sm">No matching projects.</p>
          ) : (
            <ul className="list-disc pl-5 text-sm">
              {links[key].map((name) => (
                <li key={name}>{name}</li>
              ))}
            </ul>
          )}
        </section>
      ))}

      <p className="text-xs text-xtractyl-outline/70">
        Links are only created when the whole set matches: all labels (case-sensitive, order
        ignored), for Regression and Drift also all questions, and for Comparison and Regression
        identical documents. If you expected a link and none is shown, check these points before you
        confirm — and cancel instead of uploading if the combination is not what you intended. The
        pairing of questions and labels is not checked; keep it identical yourself.
      </p>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onConfirm}
          disabled={busy}
          className="px-4 py-2 rounded text-xtractyl-white bg-xtractyl-green hover:bg-xtractyl-green/80 transition disabled:opacity-50"
        >
          Confirm and create project
        </button>
        <button
          type="button"
          onClick={onEdit}
          disabled={busy}
          className="px-4 py-2 rounded border border-xtractyl-outline/30 disabled:opacity-50"
        >
          Back to edit
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={busy}
          className="px-4 py-2 rounded border border-xtractyl-orange text-xtractyl-orange disabled:opacity-50"
        >
          Cancel and delete project
        </button>
      </div>
    </div>
  );
}
