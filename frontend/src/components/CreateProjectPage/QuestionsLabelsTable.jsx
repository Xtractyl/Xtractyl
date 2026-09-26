//src/components/CreateProjectPage/QuestionsLabelsTable.jsx

export default function QuestionsLabelsTable({ questions, labels, setQuestions, setLabels }) {
  const questionLines = (questions || "").replace(/\r\n/g, "\n").split("\n");
  const labelLines = (labels || "").replace(/\r\n/g, "\n").split("\n");
  const rowCount = Math.max(questionLines.length, labelLines.length, 1);

  const handleQuestionLineChange = (index, value) => {
    const lines = [...questionLines];
    lines[index] = value;

    // If it's the last line and not empty → append a new empty line
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

  // Pasting multi-line text into a single row distributes it across the
  // following rows instead of dumping everything into one cell.
  const handleQuestionPaste = (e, index) => {
    const pasted = e.clipboardData.getData("text");
    if (!pasted.includes("\n")) return;
    e.preventDefault();

    const pastedLines = pasted.replace(/\r\n/g, "\n").split("\n").filter((l) => l.trim() !== "");
    const lines = [...questionLines];
    pastedLines.forEach((line, i) => {
      lines[index + i] = line;
    });
    if (lines[lines.length - 1]?.trim() !== "") {
      lines.push("");
    }
    setQuestions(lines.join("\n"));
  };

  const handleLabelPaste = (e, index) => {
    const pasted = e.clipboardData.getData("text");
    if (!pasted.includes("\n")) return;
    e.preventDefault();

    const pastedLines = pasted.replace(/\r\n/g, "\n").split("\n").filter((l) => l.trim() !== "");
    const lines = [...labelLines];
    pastedLines.forEach((line, i) => {
      lines[index + i] = line;
    });
    if (lines[lines.length - 1]?.trim() !== "") {
      lines.push("");
    }
    setLabels(lines.join("\n"));
  };

  return (
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
  );
}