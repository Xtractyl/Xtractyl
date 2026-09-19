// src/pages/GetResults.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppProvider } from "../context/AppContext";
import GetResultsPage from "./GetResults.jsx";

describe("GetResults page", () => {
  it("renders the get results heading", () => {
    render(
      <AppProvider>
        <GetResultsPage />
      </AppProvider>
    );

    expect(screen.getByText("Get Results")).toBeInTheDocument();
  });
});