// src/pages/EvaluateAI.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppProvider } from "../context/AppContext";
import EvaluateAIPage from "./EvaluateAI.jsx";

describe("EvaluateAI page", () => {
  it("renders the evaluate AI heading", () => {
    render(
      <AppProvider>
        <EvaluateAIPage />
      </AppProvider>
    );

    expect(screen.getByText("Evaluate AI")).toBeInTheDocument();
  });
});