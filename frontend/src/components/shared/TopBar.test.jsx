// src/components/shared/TopBar.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import TopBar from "./TopBar.jsx";

describe("TopBar", () => {
  it("renders all workflow navigation links", () => {
    render(
      <MemoryRouter>
        <TopBar />
      </MemoryRouter>
    );

    expect(screen.getByText("Import Docs")).toBeInTheDocument();
    expect(screen.getByText("Create Labelstudio Project")).toBeInTheDocument();
    expect(screen.getByText("Upload in Labelstudio Project")).toBeInTheDocument();
    expect(screen.getByText("Start AI")).toBeInTheDocument();
    expect(screen.getByText("Review AI")).toBeInTheDocument();
    expect(screen.getByText("Get Results")).toBeInTheDocument();
    expect(screen.getByText("Evaluate AI")).toBeInTheDocument();
    expect(
      screen.getByText("Evaluation Comparison, Drift & Regression")
    ).toBeInTheDocument();
  });

  it("links the logo to the about page", () => {
    render(
      <MemoryRouter>
        <TopBar />
      </MemoryRouter>
    );

    const logoLink = screen.getByRole("link", { name: "Xtractyl Logo" });
    expect(logoLink).toHaveAttribute("href", "/aboutpage");
  });
});