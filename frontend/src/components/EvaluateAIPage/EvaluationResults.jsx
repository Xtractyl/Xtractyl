// src/components/EvaluateAIPage/EvaluationResults.jsx
import React from "react";

export default function EvaluationResults({ loading, errorMsg, result }) {
  return (
<div className="mt-8">
  <h2 className="text-xl font-semibold text-[#444038] border-b border-[#cfcab5] pb-1">
    General Project Information
  </h2>

  {result && (
    <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
      <div className="p-3 bg-[#f4f1e6] rounded border border-[#d3ccb8]">
        <div className="font-semibold text-[#23211c]">Groundtruth Project</div>
        <div className="mt-1 text-[#444038]">
          Name: <b>{result.groundtruth_project}</b>
          <br />
          ID: <span>{result.groundtruth_project_id}</span>
        </div>
      </div>
      <div className="p-3 bg-[#f4f1e6] rounded border border-[#d3ccb8]">
        <div className="font-semibold text-[#23211c]">Comparison Project</div>
        <div className="mt-1 text-[#444038]">
          Name: <b>{result.comparison_project}</b>
          <br />
          ID: <span>{result.comparison_project_id}</span>
        </div>
      </div>
    </div>
  )}
</div>
  );
}