# orchestrator/tests/unit/test_results_table_minimal.py

from domain.models.results import GetResultsTableCommand
from domain.results import build_results_table


def test_build_results_table_returns_basic_shape(monkeypatch):
    monkeypatch.setattr("domain.results.resolve_project_id", lambda token, project: 123)
    monkeypatch.setattr(
        "domain.results.fetch_tasks_page",
        lambda token, pid: ([], 0),
    )
    monkeypatch.setattr(
        "domain.results._write_results_table_csv",
        lambda columns, rows, pid, project: "/tmp/fake.csv",
    )

    cmd = GetResultsTableCommand(token="tok", project_name="my_project")
    out = build_results_table(cmd)

    assert out["columns"] == ["task_id", "filename"]
    assert out["rows"] == []
    assert out["total"] == 0
    assert out["results_output_path_csv"] == "/tmp/fake.csv"
