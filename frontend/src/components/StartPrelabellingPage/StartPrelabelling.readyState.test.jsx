import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AppProvider } from "../../context/AppContext";
import StartPrelabellingCard from "./StartPrelabellingCard.jsx";
import {
  listModels,
  getProjectsReadyForPrelabelling,
  prelabelProject,
  getPrelabelStatus,
} from "../../api/StartPrelabellingPage/api.js";

vi.mock("../../api/StartPrelabellingPage/api.js");

const READY_STATE = {
  apiToken: "tok",
  projectName: "proj-a",
  ollamaModel: "llama3",
  xtractylSystemPrompt: "Extract.",
};

const renderCard = () =>
  render(
    <AppProvider>
      <StartPrelabellingCard />
    </AppProvider>
  );

describe("StartPrelabellingCard with all parameters set", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    listModels.mockResolvedValue(["llama3"]);
    getProjectsReadyForPrelabelling.mockResolvedValue(["proj-a"]);
    Object.entries(READY_STATE).forEach(([key, value]) => localStorage.setItem(key, value));
  });

  it("starts the job with the configured parameters", async () => {
    prelabelProject.mockResolvedValue({ job_id: "job-new" });
    getPrelabelStatus.mockResolvedValue({ state: "RUNNING", progress: 0 });

    renderCard();

    const startButton = screen.getByRole("button", { name: "Start Prelabeling" });
    expect(startButton).toBeEnabled();
    await userEvent.click(startButton);

    expect(prelabelProject).toHaveBeenCalledWith({
      project_name: "proj-a",
      model: "llama3",
      system_prompt: "Extract.",
      token: "tok",
    });
    expect(await screen.findByText("Prelabeling started.")).toBeInTheDocument();
    expect(await screen.findByText("job-new")).toBeInTheDocument();
    expect(localStorage.getItem("prelabelJobId")).toBe("job-new");
  });

  it("shows the backend message when starting fails", async () => {
    prelabelProject.mockRejectedValue(new Error("Project already prelabelled"));

    renderCard();

    await userEvent.click(screen.getByRole("button", { name: "Start Prelabeling" }));

    expect(await screen.findByText("Project already prelabelled")).toBeInTheDocument();
    expect(screen.queryByText(/Job ID:/)).not.toBeInTheDocument();
  });

  it.each(Object.keys(READY_STATE))("keeps the start button disabled without %s", (missingKey) => {
    localStorage.removeItem(missingKey);

    renderCard();

    expect(screen.getByRole("button", { name: "Start Prelabeling" })).toBeDisabled();
  });
});