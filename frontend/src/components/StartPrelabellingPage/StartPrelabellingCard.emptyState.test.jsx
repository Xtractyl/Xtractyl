import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppProvider } from "../../context/AppContext";
import StartPrelabellingCard from "./StartPrelabellingCard.jsx";
import {
  listModels,
  getProjectsReadyForPrelabelling,
} from "../../api/StartPrelabellingPage/api.js";

vi.mock("../../api/StartPrelabellingPage/api.js");

describe("StartPrelabellingCard", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    listModels.mockResolvedValue([]);
    getProjectsReadyForPrelabelling.mockResolvedValue([]);
  });

  it("renders the empty form with no active job", async () => {
    render(
      <AppProvider>
        <StartPrelabellingCard />
      </AppProvider>
    );

    expect(screen.getByText("Start AI")).toBeInTheDocument();
    expect(screen.getByText("Select installed model")).toBeInTheDocument();
    expect(screen.getByText("System prompt")).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Start Prelabeling" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();

    expect(screen.queryByText(/^Status:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Job ID:/)).not.toBeInTheDocument();
  });
});
