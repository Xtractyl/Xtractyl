// frontend/src/components/EvaluateAIPage/EvaluationResults.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import EvaluationResults from "./EvaluationResults.jsx";

const result = {
  groundtruth_project: "gt-project",
  groundtruth_project_id: 11,
  comparison_project: "cmp-project",
  comparison_project_id: 22,
  run_at_raw: "2026-01-02T03:04:05Z",
  metrics: {
    micro: {
      precision: 0.5,
      recall: 0.25,
      f1: 0.333333,
      accuracy: 0.75,
      tp: 1,
      fp: 2,
      fn: 3,
      tn: 4,
    },
    per_label: { name: { precision: 0.9, recall: 0.8, f1: 0.7 } },
    task_metrics: [
      {
        filename: "a.html",
        per_label: { name: { gt: "gt-value", pred: "pred-value", status: "mismatch" } },
        meta: {
          model: "llama",
          system_prompt: "Be precise",
          raw_llm_answers: { name: { answer: "raw-answer" } },
          dom_match_by_label: { name: true },
          performance: {
            events: [{ name: "llm.call", ms: 12.34, tags: { label: "name", status: "ok" } }],
          },
        },
      },
    ],
    performance: {
      task_ms_total_avg: 101,
      task_ms_dom_extract_avg: 102,
      task_ms_dom_match_avg: 103,
      task_ms_llm_total_avg: 104,
      n_tasks_with_perf: 5,
      task_ms_total_p95: 200.55,
      task_ms_llm_total_p95: 150.25,
    },
  },
};

describe("EvaluationResults", () => {
  it("shows a loading hint while loading", () => {
    render(<EvaluationResults loading={true} errorMsg="" result={null} />);

    expect(screen.getByText("Running evaluation…")).toBeInTheDocument();
  });

  it("shows the error message", () => {
    render(<EvaluationResults loading={false} errorMsg="it failed" result={null} />);

    expect(screen.getByText("it failed")).toBeInTheDocument();
  });

  it("renders nothing without a result", () => {
    const { container } = render(<EvaluationResults loading={false} errorMsg="" result={null} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("shows the project information", () => {
    render(<EvaluationResults loading={false} errorMsg="" result={result} />);

    expect(screen.getByText("gt-project")).toBeInTheDocument();
    expect(screen.getByText("cmp-project")).toBeInTheDocument();
    expect(screen.getByText(/ID: 11/)).toBeInTheDocument();
    expect(screen.getByText(/ID: 22/)).toBeInTheDocument();
    expect(screen.getByText(/Model: llama/)).toBeInTheDocument();
  });

  it("shows the system prompt", () => {
    render(<EvaluationResults loading={false} errorMsg="" result={result} />);

    expect(screen.getByText("Be precise")).toBeInTheDocument();
  });

  it("shows the micro metrics with three decimals and the counts", () => {
    render(<EvaluationResults loading={false} errorMsg="" result={result} />);

    expect(screen.getByText("0.500")).toBeInTheDocument();
    expect(screen.getByText("0.250")).toBeInTheDocument();
    expect(screen.getByText("0.333")).toBeInTheDocument();
    expect(screen.getByText("0.750")).toBeInTheDocument();
    expect(screen.getByText(/TP 1 · FP 2 · FN 3 · TN 4/)).toBeInTheDocument();
  });

  it("shows the per-label metrics", () => {
    render(<EvaluationResults loading={false} errorMsg="" result={result} />);

    expect(screen.getByText("0.900")).toBeInTheDocument();
    expect(screen.getByText("0.800")).toBeInTheDocument();
    expect(screen.getByText("0.700")).toBeInTheDocument();
  });

  it("shows the per-task details with raw answer, DOM match and status", () => {
    render(<EvaluationResults loading={false} errorMsg="" result={result} />);

    expect(screen.getByText("a.html")).toBeInTheDocument();
    expect(screen.getByText("gt-value")).toBeInTheDocument();
    expect(screen.getByText("pred-value")).toBeInTheDocument();
    expect(screen.getByText("raw-answer")).toBeInTheDocument();
    expect(screen.getByText("ok")).toBeInTheDocument();
    expect(screen.getByText("mismatch")).toBeInTheDocument();
  });

  it("shows the LLM call durations", () => {
    render(<EvaluationResults loading={false} errorMsg="" result={result} />);

    expect(screen.getByText("name (ok)")).toBeInTheDocument();
    expect(screen.getByText("12.3")).toBeInTheDocument();
  });

  it("shows the aggregated backend performance when present", () => {
    render(<EvaluationResults loading={false} errorMsg="" result={result} />);

    expect(screen.getByText("Performance (Backend)")).toBeInTheDocument();
    expect(screen.getByText("101.000")).toBeInTheDocument();
    expect(screen.getByText(/Number of Tasks: 5/)).toBeInTheDocument();
    expect(screen.getByText(/200\.6 ms/)).toBeInTheDocument();
    expect(screen.getByText(/150\.3 ms/)).toBeInTheDocument();
  });

  it("hides the backend performance section when there is none", () => {
    const withoutPerformance = {
      ...result,
      metrics: { ...result.metrics, performance: undefined },
    };

    render(<EvaluationResults loading={false} errorMsg="" result={withoutPerformance} />);

    expect(screen.queryByText("Performance (Backend)")).not.toBeInTheDocument();
  });

  it("accepts the payload wrapped in data", () => {
    render(<EvaluationResults loading={false} errorMsg="" result={{ data: result }} />);

    expect(screen.getByText("gt-project")).toBeInTheDocument();
  });

  it("accepts the payload wrapped in logs", () => {
    render(<EvaluationResults loading={false} errorMsg="" result={{ logs: result }} />);

    expect(screen.getByText("cmp-project")).toBeInTheDocument();
  });

  it("renders without metrics instead of crashing", () => {
    render(
      <EvaluationResults loading={false} errorMsg="" result={{ groundtruth_project: "gt-only" }} />
    );

    expect(screen.getByText("gt-only")).toBeInTheDocument();
    expect(screen.getByText("Overall Metrics (Micro)")).toBeInTheDocument();
  });
});
