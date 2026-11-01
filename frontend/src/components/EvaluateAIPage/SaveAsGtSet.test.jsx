// frontend/src/components/EvaluateAIPage/SaveAsGtSet.test.jsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SaveAsGtSet from "./SaveAsGtSet.jsx";
import { saveAsGtSet, getProjectsReadyForGroundtruth } from "../../api/EvaluateAIPage/api.js";

vi.mock("../../api/EvaluateAIPage/api.js");

async function renderWithCandidates(props = {}, candidates = ["p1", "p2"]) {
  getProjectsReadyForGroundtruth.mockResolvedValue(candidates);
  render(<SaveAsGtSet apiToken="tok" {...props} />);
  await screen.findByRole("option", { name: candidates[0] });
}

const select = () => screen.getByRole("combobox");
const externalButton = () => screen.getByRole("button", { name: "Save as External GT" });
const internalButton = () => screen.getByRole("button", { name: "Save as Internal GT" });
const choose = (name) => fireEvent.change(select(), { target: { value: name } });

describe("SaveAsGtSet", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("loads the candidates once on mount and offers them as options", async () => {
    await renderWithCandidates();

    expect(getProjectsReadyForGroundtruth).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("option", { name: "p2" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "-- Select Project --" })).toBeInTheDocument();
  });

  it("shows the load error", async () => {
    getProjectsReadyForGroundtruth.mockRejectedValue(new Error("no list"));

    render(<SaveAsGtSet apiToken="tok" />);

    expect(await screen.findByText("no list")).toBeInTheDocument();
  });

  it("uses a default message when the load error has none", async () => {
    getProjectsReadyForGroundtruth.mockRejectedValue(new Error(""));

    render(<SaveAsGtSet apiToken="tok" />);

    expect(await screen.findByText("Failed to load projects.")).toBeInTheDocument();
  });

  it("disables both buttons until a project is selected", async () => {
    await renderWithCandidates();

    expect(externalButton()).toBeDisabled();
    expect(internalButton()).toBeDisabled();

    choose("p1");

    expect(externalButton()).toBeEnabled();
    expect(internalButton()).toBeEnabled();
  });

  it("saves as external with token, project and scope, then resets and reloads", async () => {
    const onSuccess = vi.fn();
    saveAsGtSet.mockResolvedValue({ status: "ok" });
    await renderWithCandidates({ onSuccess });

    choose("p1");
    fireEvent.click(externalButton());

    expect(
      await screen.findByText('"p1" successfully saved as external GT set.')
    ).toBeInTheDocument();
    expect(saveAsGtSet).toHaveBeenCalledWith("tok", "p1", "external");
    expect(select()).toHaveValue("");
    expect(getProjectsReadyForGroundtruth).toHaveBeenCalledTimes(2);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("saves as internal with the internal scope", async () => {
    saveAsGtSet.mockResolvedValue({ status: "ok" });
    await renderWithCandidates();

    choose("p2");
    fireEvent.click(internalButton());

    expect(
      await screen.findByText('"p2" successfully saved as internal GT set.')
    ).toBeInTheDocument();
    expect(saveAsGtSet).toHaveBeenCalledWith("tok", "p2", "internal");
  });

  it("works without an onSuccess callback", async () => {
    saveAsGtSet.mockResolvedValue({ status: "ok" });
    await renderWithCandidates();

    choose("p1");
    fireEvent.click(externalButton());

    expect(await screen.findByText(/successfully saved/)).toBeInTheDocument();
  });

  it("shows Saving… on both buttons and disables them while saving", async () => {
    saveAsGtSet.mockReturnValue(new Promise(() => {}));
    await renderWithCandidates();

    choose("p1");
    fireEvent.click(externalButton());

    const saving = await screen.findAllByText("Saving…");
    expect(saving).toHaveLength(2);
    saving.forEach((button) => expect(button).toBeDisabled());
  });

  it("shows the error, keeps the selection and does not call onSuccess when saving fails", async () => {
    const onSuccess = vi.fn();
    saveAsGtSet.mockRejectedValue(new Error("nope"));
    await renderWithCandidates({ onSuccess });

    choose("p1");
    fireEvent.click(externalButton());

    expect(await screen.findByText("nope")).toBeInTheDocument();
    expect(select()).toHaveValue("p1");
    expect(onSuccess).not.toHaveBeenCalled();
    expect(externalButton()).toBeEnabled();
  });

  it("uses a default message when the save error has none", async () => {
    saveAsGtSet.mockRejectedValue(new Error(""));
    await renderWithCandidates();

    choose("p1");
    fireEvent.click(externalButton());

    expect(await screen.findByText("Failed to save as GT set.")).toBeInTheDocument();
  });

  it("clears a previous success message when saving again fails", async () => {
    saveAsGtSet.mockResolvedValueOnce({ status: "ok" }).mockRejectedValueOnce(new Error("second"));
    await renderWithCandidates();

    choose("p1");
    fireEvent.click(externalButton());
    await screen.findByText(/successfully saved/);

    choose("p2");
    fireEvent.click(externalButton());

    expect(await screen.findByText("second")).toBeInTheDocument();
    expect(screen.queryByText(/successfully saved/)).not.toBeInTheDocument();
  });

  it("clears an old load error when the candidates are loaded again", async () => {
    saveAsGtSet.mockResolvedValue({ status: "ok" });
    getProjectsReadyForGroundtruth
      .mockResolvedValueOnce(["p1"])
      .mockRejectedValueOnce(new Error("reload failed"))
      .mockResolvedValueOnce(["p1"]);
    render(<SaveAsGtSet apiToken="tok" />);
    await screen.findByRole("option", { name: "p1" });

    choose("p1");
    fireEvent.click(externalButton());
    expect(await screen.findByText("reload failed")).toBeInTheDocument();

    choose("p1");
    fireEvent.click(externalButton());

    await waitFor(() => expect(screen.queryByText("reload failed")).not.toBeInTheDocument());
    expect(getProjectsReadyForGroundtruth).toHaveBeenCalledTimes(3);
  });
});
