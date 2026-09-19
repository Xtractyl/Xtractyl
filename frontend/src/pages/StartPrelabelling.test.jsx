// src/pages/StartPrelabelling.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppProvider } from "../context/AppContext";
import StartPrelabellingPage from "./StartPrelabelling.jsx";

describe("StartPrelabelling page", () => {
  it("renders the start AI heading", () => {
    render(
      <AppProvider>
        <StartPrelabellingPage />
      </AppProvider>
    );

    expect(screen.getByText("Start AI")).toBeInTheDocument();
  });
});