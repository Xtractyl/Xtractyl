// src/pages/EvaluationDrift.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import EvaluationDriftPage from "./EvaluationDrift.jsx";

describe("EvaluationDrift page", () => {
  it("renders the drift and regression heading", () => {
    render(<EvaluationDriftPage />);

    expect(
      screen.getByText("Evaluation Comparison, Drift & Regression")
    ).toBeInTheDocument();
  });
});