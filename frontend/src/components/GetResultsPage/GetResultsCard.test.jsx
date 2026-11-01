// frontend/src/components/GetResultsPage/GetResultsCard.test.jsx  (neu)
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AppProvider } from "../../context/AppContext.jsx";
import GetResultsCard from "./GetResultsCard.jsx";
import { getProjectsReadyForResults, getResultsTable } from "../../api/GetResultsPage/api.js";

vi.mock("../../api/GetResultsPage/api.js");

const TABLE = {
  columns: ["task_id", "filename", "name__pred"],
  rows: [{ task_id: 1, filename: "a.html", name__pred: "Alice" }],
  total: 1,
};

function renderCard() {
  return render(
    <AppProvider>
      <GetResultsCard />
    </AppProvider>
  );
}

async function selectProject(user, name) {
  await screen.findByRole("option", { name });
  await user.selectOptions(screen.getByRole("combobox"), name);
}

describe("GetResultsCard", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
    getProjectsReadyForResults.mockResolvedValue(["proj-a", "proj-b"]);
  });

  it("disables Submit until a project is selected and shows no table yet", async () => {
    const user = userEvent.setup();
    renderCard();

    const submit = screen.getByRole("button", { name: "Submit" });
    expect(submit).toBeDisabled();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();

    await selectProject(user, "proj-a");

    expect(submit).toBeEnabled();
  });

  it("loads the results for the selected project and shows them in a table", async () => {
    getResultsTable.mockResolvedValue(TABLE);
    const user = userEvent.setup();
    renderCard();

    await selectProject(user, "proj-a");
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(getResultsTable).toHaveBeenCalledWith({ projectName: "proj-a" });
    expect(await screen.findByText("Alice")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "name__pred" })).toBeInTheDocument();
  });

  it("shows the error message when loading the results fails", async () => {
    getResultsTable.mockRejectedValue(new Error("RUN_NOT_DONE"));
    const user = userEvent.setup();
    renderCard();

    await selectProject(user, "proj-a");
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByText("RUN_NOT_DONE")).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("shows 'No data.' when the table has columns but no rows", async () => {
    getResultsTable.mockResolvedValue({ columns: ["task_id", "filename"], rows: [], total: 0 });
    const user = userEvent.setup();
    renderCard();

    await selectProject(user, "proj-a");
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByText("No data.")).toBeInTheDocument();
  });

  it("hides the previous results when another project is selected", async () => {
    getResultsTable.mockResolvedValue(TABLE);
    const user = userEvent.setup();
    renderCard();

    await selectProject(user, "proj-a");
    await user.click(screen.getByRole("button", { name: "Submit" }));
    expect(await screen.findByText("Alice")).toBeInTheDocument();

    await user.selectOptions(screen.getByRole("combobox"), "proj-b");

    expect(screen.queryByText("Alice")).not.toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("clears an earlier error when another project is selected", async () => {
    getResultsTable.mockRejectedValue(new Error("RUN_NOT_DONE"));
    const user = userEvent.setup();
    renderCard();

    await selectProject(user, "proj-a");
    await user.click(screen.getByRole("button", { name: "Submit" }));
    expect(await screen.findByText("RUN_NOT_DONE")).toBeInTheDocument();

    await user.selectOptions(screen.getByRole("combobox"), "proj-b");

    expect(screen.queryByText("RUN_NOT_DONE")).not.toBeInTheDocument();
  });
});
