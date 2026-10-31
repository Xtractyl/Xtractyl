// frontend/src/components/EvaluateAIPage/EvaluateAICard.test.jsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AppProvider } from "../../context/AppContext";
import EvaluateAICard from "./EvaluateAICard.jsx";
import {
  getProjectsReadyForGroundtruth,
  getProjectsReadyForComparison,
  getGroundtruthProjectsForComparison,
  saveAsGtSet,
  evaluateAI,
} from "../../api/EvaluateAIPage/api.js";

vi.mock("../../api/EvaluateAIPage/api.js");

const evaluation = {
  groundtruth_project: "gtA",
  groundtruth_project_id: 1,
  comparison_project: "cmp1",
  comparison_project_id: 2,
  metrics: { micro: {}, per_label: {}, task_metrics: [] },
};

function renderCard() {
  return render(
    <AppProvider>
      <EvaluateAICard />
    </AppProvider>
  );
}

const showEvaluationButton = () => screen.findByRole("button", { name: "Show Evaluation" });

describe("EvaluateAICard", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    localStorage.clear();
    getProjectsReadyForGroundtruth.mockResolvedValue(["candidate"]);
    getProjectsReadyForComparison.mockResolvedValue(["cmp1", "cmp2"]);
    getGroundtruthProjectsForComparison.mockImplementation(async (comparison) =>
      comparison === "cmp1" ? ["gtA", "gtB"] : ["gtC"]
    );
    evaluateAI.mockResolvedValue(evaluation);
  });

  it("loads the comparison projects and the matching groundtruth sets on start", async () => {
    renderCard();

    expect(await screen.findByDisplayValue("cmp1")).toBeInTheDocument();
    expect(await screen.findByDisplayValue("gtA")).toBeInTheDocument();
    expect(getGroundtruthProjectsForComparison).toHaveBeenCalledWith("cmp1");
  });

  it("shows an empty-state hint when no project is ready for evaluation", async () => {
    getProjectsReadyForComparison.mockResolvedValue([]);

    renderCard();

    expect(await screen.findByText("No projects available for evaluation.")).toBeInTheDocument();
    expect(getGroundtruthProjectsForComparison).not.toHaveBeenCalled();
  });

  it("shows the error when the projects cannot be loaded", async () => {
    getProjectsReadyForComparison.mockRejectedValue(new Error("db down"));

    renderCard();

    expect(await screen.findByText("db down")).toBeInTheDocument();
  });

  it("loads the groundtruth sets of another comparison project when it is selected", async () => {
    renderCard();
    fireEvent.change(await screen.findByDisplayValue("cmp1"), { target: { value: "cmp2" } });

    expect(await screen.findByDisplayValue("gtC")).toBeInTheDocument();
    expect(getGroundtruthProjectsForComparison).toHaveBeenLastCalledWith("cmp2");
  });

  it("runs the evaluation for the selected pair and shows the result", async () => {
    renderCard();
    const button = await showEvaluationButton();
    await waitFor(() => expect(button).toBeEnabled());

    fireEvent.click(button);

    expect(await screen.findByText("Project Information")).toBeInTheDocument();
    expect(evaluateAI).toHaveBeenCalledWith("gtA", "cmp1");
  });

  it("shows the error message when the evaluation fails", async () => {
    evaluateAI.mockRejectedValue(new Error("No evaluation found"));
    renderCard();
    const button = await showEvaluationButton();
    await waitFor(() => expect(button).toBeEnabled());

    fireEvent.click(button);

    expect(await screen.findByText("No evaluation found")).toBeInTheDocument();
    expect(screen.queryByText("Project Information")).not.toBeInTheDocument();
  });

  it("keeps the evaluation button disabled while no groundtruth set is selected", async () => {
    getGroundtruthProjectsForComparison.mockResolvedValue([]);

    renderCard();

    expect(await showEvaluationButton()).toBeDisabled();
    expect(
      await screen.findByText("No groundtruth project available for this comparison project.")
    ).toBeInTheDocument();
  });

  it("reloads projects and groundtruth sets after a new GT set was saved", async () => {
    localStorage.setItem("apiToken", "tok");
    saveAsGtSet.mockResolvedValue({ status: "ok" });
    renderCard();
    await screen.findByDisplayValue("gtA");
    expect(getProjectsReadyForComparison).toHaveBeenCalledTimes(1);
    expect(getGroundtruthProjectsForComparison).toHaveBeenCalledTimes(1);

    fireEvent.change(screen.getByDisplayValue("-- Select Project --"), {
      target: { value: "candidate" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save as External GT" }));

    await screen.findByText(/successfully saved/);
    await waitFor(() => expect(getProjectsReadyForComparison).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(getGroundtruthProjectsForComparison).toHaveBeenCalledTimes(2));
    expect(saveAsGtSet).toHaveBeenCalledWith("tok", "candidate", "external");
  });
});
