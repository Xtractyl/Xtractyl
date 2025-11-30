  // frontend/src/components/EvaluateAIPage/EvaluateAICard.jsx
import React, { useCallback, useEffect, useMemo, useState } from "react";

export default function EvaluateAICard({ apiToken, projectName}) {
    return (
        <div className="p-8 bg-[#e6e2cf] min-h-screen text-[#23211c]">
        <h1 className="text-2xl font-semibold mb-4">Evaluate AI</h1>
        <p className="text-gray-600">
          This feature will be included in later releases. It will allow you
          to compare a model against others using metrics like precision,
          recall, and F1.
        </p>
      </div>
    );
  }

