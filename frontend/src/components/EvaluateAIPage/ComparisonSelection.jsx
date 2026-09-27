// src/components/EvaluateAIPage/ComparisonSelection.jsx
export default function ComparisonSelection({
  projects,
  gtSets,
  loading,
  errorMsg,
  groundtruthProject,
  setGroundtruthProject,
  comparisonProject,
  setComparisonProject,
  onSubmit,
}) {

  const comparisonOptions = projects.filter((name) => !gtSets.includes(name));

  
  return (
    <div>
      <p className="text-xs text-xtractyl-outline/70 mb-2">
        You can click into the question/label field and paste all
        questions/labels from a existing ground truth set (ctrl+v to paste)
      </p>

      <div className="mt-4 border border-xtractyl-outline/30 rounded-md overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-[3rem,1fr,1fr] bg-xtractyl-offwhite text-xs font-semibold px-3 py-2 border-b border-xtractyl-outline/30">
          <div>#</div>
          <div className="border-l border-xtractyl-outline/30 border-r pl-2 pr-2">Question</div>
          <div>Label</div>
        </div>

        {/* Rows */}
        <div className="divide-y divide-xtractyl-outline/20">
          {Array.from({ length: rowCount }).map((_, idx) => (
            <div key={idx} className="grid grid-cols-[3rem,1fr,1fr] px-3 py-2 items-center">
              <div className="text-xs  text-xtractyl-outline/60">{idx + 1}</div>

              <input
                type="text"
                value={questionLines[idx] || ""}
                onChange={(e) => handleQuestionLineChange(idx, e.target.value)}
                onPaste={(e) => handleQuestionPaste(e, idx)}
                placeholder={idx === 0 ? "e.g., What is the patient ID?" : ""}
                className="w-full text-sm px-2 py-1 border border-xtractyl-outline/20 rounded-md whitespace-nowrap overflow-x-auto overflow-y-hidden focus:outline-none focus:ring-1 focus:ring-xtractyl-lightgreen"
              />

              <input
                type="text"
                value={labelLines[idx] || ""}
                onChange={(e) => handleLabelLineChange(idx, e.target.value)}
                onPaste={(e) => handleLabelPaste(e, idx)}
                placeholder={idx === 0 ? "e.g., Patient ID" : ""}
                className="w-full text-sm px-2 py-1 border border-xtractyl-outline/20 rounded-md whitespace-nowrap overflow-x-auto overflow-y-hidden focus:outline-none focus:ring-1 focus:ring-xtractyl-lightgreen"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}