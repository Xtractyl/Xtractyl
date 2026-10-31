// frontend/src/components/EvaluateAIPage/ComparisonSelection.test.jsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import ComparisonSelection from "./ComparisonSelection.jsx";

function renderSelection(overrides = {}) {
  const props = {
    projects: ["p1", "p2"],
    loading: false,
    errorMsg: "",
    compatibleGtSets: ["gt1", "gt2"],
    compatibleLoading: false,
    compatibleError: "",
    groundtruthProject: "gt1",
    setGroundtruthProject: vi.fn(),
    comparisonProject: "p1",
    setComparisonProject: vi.fn(),
    onSubmit: vi.fn(),
    ...overrides,
  };
  render(<ComparisonSelection {...props} />);
  return props;
}

const optionTexts = (select) =>
  within(select)
    .getAllByRole("option")
    .map((o) => o.textContent);

const submitButton = () => screen.getByRole("button", { name: "Show Evaluation" });

describe("ComparisonSelection", () => {
  it("shows a loading hint and no selects while the projects load", () => {
    renderSelection({ loading: true });

    expect(screen.getByText("Loading projects…")).toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("shows the error message instead of the selects", () => {
    renderSelection({ errorMsg: "boom" });

    expect(screen.getByText("boom")).toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("shows an empty-state hint when there are no projects", () => {
    renderSelection({ projects: [] });

    expect(screen.getByText("No projects available for evaluation.")).toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("offers the projects and the compatible groundtruth sets as options", () => {
    renderSelection();

    const [comparisonSelect, groundtruthSelect] = screen.getAllByRole("combobox");
    expect(optionTexts(comparisonSelect)).toEqual(["p1", "p2"]);
    expect(optionTexts(groundtruthSelect)).toEqual(["gt1", "gt2"]);
    expect(comparisonSelect).toHaveValue("p1");
    expect(groundtruthSelect).toHaveValue("gt1");
  });

  it("reports a changed comparison project", () => {
    const props = renderSelection();

    fireEvent.change(screen.getAllByRole("combobox")[0], { target: { value: "p2" } });

    expect(props.setComparisonProject).toHaveBeenCalledWith("p2");
  });

  it("reports a changed groundtruth project", () => {
    const props = renderSelection();

    fireEvent.change(screen.getAllByRole("combobox")[1], { target: { value: "gt2" } });

    expect(props.setGroundtruthProject).toHaveBeenCalledWith("gt2");
  });

  it("shows a loading hint while the compatible sets load", () => {
    renderSelection({ compatibleLoading: true });

    expect(screen.getByText("Loading groundtruth projects…")).toBeInTheDocument();
  });

  it("shows the error of the compatible sets", () => {
    renderSelection({ compatibleError: "no sets" });

    expect(screen.getByText("no sets")).toBeInTheDocument();
  });

  it("shows a hint when no groundtruth project is compatible", () => {
    renderSelection({ compatibleGtSets: [], groundtruthProject: "" });

    expect(
      screen.getByText("No groundtruth project available for this comparison project.")
    ).toBeInTheDocument();
  });

  it("does not show the empty hint while loading or after an error", () => {
    const { rerender } = render(<div />);
    rerender(<div />);

    renderSelection({ compatibleGtSets: [], groundtruthProject: "", compatibleLoading: true });
    expect(
      screen.queryByText("No groundtruth project available for this comparison project.")
    ).not.toBeInTheDocument();
  });

  it("calls onSubmit when both projects are selected", () => {
    const props = renderSelection();

    expect(submitButton()).toBeEnabled();
    fireEvent.click(submitButton());

    expect(props.onSubmit).toHaveBeenCalledTimes(1);
  });

  it("disables the button without a groundtruth project", () => {
    renderSelection({ groundtruthProject: "" });

    expect(submitButton()).toBeDisabled();
  });

  it("disables the button without a comparison project", () => {
    renderSelection({ comparisonProject: "" });

    expect(submitButton()).toBeDisabled();
  });

  it("disables the button while the compatible sets are loading", () => {
    renderSelection({ compatibleLoading: true });

    expect(submitButton()).toBeDisabled();
  });
});
