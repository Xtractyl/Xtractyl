// src/pages/CreateProject.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppProvider } from "../context/AppContext";
import CreateProjectPage from "./CreateProject.jsx";

describe("CreateProject page", () => {
  it("renders the create project heading", () => {
    render(
      <AppProvider>
        <CreateProjectPage />
      </AppProvider>
    );

    expect(screen.getByText("Create Project")).toBeInTheDocument();
  });
});