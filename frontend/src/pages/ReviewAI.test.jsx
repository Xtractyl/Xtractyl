// src/pages/ReviewAI.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppProvider } from "../context/AppContext";
import ReviewAI from "./ReviewAI.jsx";

describe("ReviewAI page", () => {
  it("renders the review AI heading", () => {
    render(
      <AppProvider>
        <ReviewAI />
      </AppProvider>
    );

    expect(screen.getByText("Review AI")).toBeInTheDocument();
  });
});