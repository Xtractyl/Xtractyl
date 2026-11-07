// frontend/src/components/CreateProjectPage/CreateProjectCard.test.jsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AppProvider } from "../../context/AppContext";
import CreateProjectCard from "./CreateProjectCard.jsx";
import {
  getProjectsReadyForCreation,
  fetchGroundtruthQuestionsAndLabels,
  getProjectLinks,
  createProject,
  discardProject,
} from "../../api/CreateProjectPage/api.js";

vi.mock("../../api/CreateProjectPage/api.js");

const links = { comparison: ["projA"], regression: [], drift: ["projB"] };

function renderCard() {
  return render(
    <AppProvider>
      <CreateProjectCard />
    </AppProvider>
  );
}

async function fillAndSubmit() {
  await screen.findByRole("option", { name: "proj1" });
  fireEvent.change(screen.getByLabelText(/Select converted project/), {
    target: { value: "proj1" },
  });
  fireEvent.change(screen.getByPlaceholderText("e.g., What is the patient ID?"), {
    target: { value: "When?" },
  });
  fireEvent.change(screen.getByPlaceholderText("e.g., Patient ID"), {
    target: { value: "Date" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create project" }));
}

const comparisonHeading = () => screen.queryByRole("heading", { name: "Comparison" });

describe("CreateProjectCard", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    localStorage.clear();
    localStorage.setItem("apiToken", "tok");
    getProjectsReadyForCreation.mockResolvedValue(["proj1"]);
    fetchGroundtruthQuestionsAndLabels.mockResolvedValue({});
    getProjectLinks.mockResolvedValue(links);
    createProject.mockResolvedValue({ project_id: 1 });
    discardProject.mockResolvedValue({ status: "discarded" });
  });

  it("shows the links the project would get before anything is created", async () => {
    renderCard();

    await fillAndSubmit();

    expect(await screen.findByText("projA")).toBeInTheDocument();
    expect(screen.getByText("projB")).toBeInTheDocument();
    expect(getProjectLinks).toHaveBeenCalledWith({
      title: "proj1",
      questions: ["When?"],
      labels: ["Date"],
    });
    expect(createProject).not.toHaveBeenCalled();
  });

  it("creates the project after the user confirmed", async () => {
    renderCard();
    await fillAndSubmit();

    fireEvent.click(await screen.findByRole("button", { name: "Confirm and create project" }));

    expect(await screen.findByText("Project created successfully.")).toBeInTheDocument();
    expect(createProject).toHaveBeenCalledWith({
      title: "proj1",
      questions: ["When?"],
      labels: ["Date"],
      token: "tok",
    });
    expect(comparisonHeading()).not.toBeInTheDocument();
  });

  it("discards the project and reloads the dropdown when the user cancels", async () => {
    renderCard();
    await fillAndSubmit();

    fireEvent.click(await screen.findByRole("button", { name: "Cancel and delete project" }));

    expect(await screen.findByText("Project discarded.")).toBeInTheDocument();
    expect(discardProject).toHaveBeenCalledWith("proj1");
    expect(createProject).not.toHaveBeenCalled();
    expect(comparisonHeading()).not.toBeInTheDocument();
    await waitFor(() => expect(getProjectsReadyForCreation).toHaveBeenCalledTimes(2));
  });

  it("lets the user go back and edit without deleting anything", async () => {
    renderCard();
    await fillAndSubmit();

    fireEvent.click(await screen.findByRole("button", { name: "Back to edit" }));

    expect(comparisonHeading()).not.toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g., Patient ID")).toBeEnabled();
    expect(discardProject).not.toHaveBeenCalled();
    expect(createProject).not.toHaveBeenCalled();
  });

  it("locks the form while the links are shown", async () => {
    renderCard();
    await fillAndSubmit();

    await screen.findByText("projA");

    expect(screen.getByPlaceholderText("e.g., Patient ID")).toBeDisabled();
  });

  it("shows the error when the check fails and shows no links", async () => {
    getProjectLinks.mockRejectedValue(new Error("PDF conversion must finish first"));
    renderCard();

    await fillAndSubmit();

    expect(await screen.findByText("PDF conversion must finish first")).toBeInTheDocument();
    expect(comparisonHeading()).not.toBeInTheDocument();
  });

  it("keeps the links open when creating the project fails", async () => {
    createProject.mockRejectedValue(new Error("Label Studio is down"));
    renderCard();
    await fillAndSubmit();

    fireEvent.click(await screen.findByRole("button", { name: "Confirm and create project" }));

    expect(await screen.findByText("Label Studio is down")).toBeInTheDocument();
    expect(comparisonHeading()).toBeInTheDocument();
  });
});
