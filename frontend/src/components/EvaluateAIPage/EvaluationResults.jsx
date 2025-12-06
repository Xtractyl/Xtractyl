// src/components/EvaluateAIPage/EvaluationResults.jsx
import React from "react";

export default function EvaluationResults() {
  return (
    <div className="mt-12">

      {/* Page Title */}
      <h1 className="text-2xl font-semibold mb-6 text-[#23211c]">
        Evaluation Results
      </h1>

      {/* SECTION 1 — GENERAL PROJECT INFORMATION */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold text-[#444038] border-b border-[#cfcab5] pb-1">
          General Project Information
        </h2>
      </div>

      {/* SECTION 2 — OVERALL EVALUATION METRICS */}
      <div className="mt-10">
        <h2 className="text-xl font-semibold text-[#444038] border-b border-[#cfcab5] pb-1">
          Overall Evaluation Metrics
        </h2>
      </div>

      {/* SECTION 3 — METRICS BY TASK */}
      <div className="mt-10">
        <h2 className="text-xl font-semibold text-[#444038] border-b border-[#cfcab5] pb-1">
          Evaluation Metrics by Task
        </h2>
      </div>

      {/* SECTION 4 — ANSWER COMPARISON */}
      <div className="mt-10">
        <h2 className="text-xl font-semibold text-[#444038] border-b border-[#cfcab5] pb-1">
          Comparison of Answers
        </h2>
      </div>

    </div>
  );
}