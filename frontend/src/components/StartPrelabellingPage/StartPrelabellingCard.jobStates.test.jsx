import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AppProvider } from "../../context/AppContext";
import StartPrelabellingCard from "./StartPrelabellingCard.jsx";
import {
  listModels,
  getProjectsReadyForPrelabelling,
  getPrelabelStatus,
  cancelPrelabel,
} from "../../api/StartPrelabellingPage/api.js";

vi.mock("../../api/StartPrelabellingPage/api.js");

const RESUME = "You can resume it the same way you started it.";

const renderCard = () =>
  render(
    <AppProvider>
      <StartPrelabellingCard />
    </AppProvider>
  );

describe("StartPrelabellingCard with an existing job", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    listModels.mockResolvedValue([]);
    getProjectsReadyForPrelabelling.mockResolvedValue([]);
    localStorage.setItem("prelabelJobId", "job-1");
  });

  it("shows status, progress and job id while running", async () => {
    getPrelabelStatus.mockResolvedValue({ state: "RUNNING", progress: 40 });

    renderCard();

    expect(await screen.findByText(/Status: RUNNING — 40%/)).toBeInTheDocument();
    expect(screen.getByText("job-1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Start Prelabeling" })).toBeDisabled();
  });

  it.each([
    ["DONE", "Prelabeling finished successfully."],
    ["INCOMPLETE", `Prelabeling finished, but some tasks were not successful. ${RESUME}`],
    ["CANCELLED", `Prelabeling was cancelled. ${RESUME}`],
  ])("shows the outcome message and clears the job when state is %s", async (state, message) => {
    getPrelabelStatus.mockResolvedValue({ state, progress: 100 });

    renderCard();

    expect(await screen.findByText(message)).toBeInTheDocument();
    expect(screen.queryByText(/^Status:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Job ID:/)).not.toBeInTheDocument();
    await waitFor(() => expect(localStorage.getItem("prelabelJobId")).toBe(""));
  });

  it("appends the backend error to the failure message", async () => {
    getPrelabelStatus.mockResolvedValue({ state: "FAILED", progress: 10, error: "Model not found" });

    renderCard();

    expect(
      await screen.findByText(`Prelabeling failed. ${RESUME} Model not found`)
    ).toBeInTheDocument();
  });

  it("drops the job silently when the backend does not know it", async () => {
    getPrelabelStatus.mockRejectedValue({ status: 404 });

    renderCard();

    await waitFor(() => expect(screen.queryByText(/Job ID:/)).not.toBeInTheDocument());
    expect(localStorage.getItem("prelabelJobId")).toBe("");
  });

  it("calls cancelPrelabel with the job id and shows the result", async () => {
    getPrelabelStatus.mockResolvedValueOnce({ state: "RUNNING", progress: 40 });
    getPrelabelStatus.mockResolvedValue({ state: "CANCEL_REQUESTED", progress: 40 });
    cancelPrelabel.mockResolvedValue({});

    renderCard();

    const cancelButton = await screen.findByRole("button", { name: "Cancel" });
    await waitFor(() => expect(cancelButton).toBeEnabled());
    await userEvent.click(cancelButton);

    expect(cancelPrelabel).toHaveBeenCalledWith("job-1");
    expect(await screen.findByText("Cancel requested.")).toBeInTheDocument();
  });
});