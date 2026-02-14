import json
from pathlib import Path

from domain.models.results import GetResultsTableCommand
from domain.results import build_results_table


def test_build_results_table_minimal_fixture(monkeypatch):
    # Load captured input fixture
    fixture_path = Path(
        "tests/fixtures/results/build_results_table_minimal__tasks_page__SYNTHETIC_DATA.json"
    )
    fx = json.loads(fixture_path.read_text(encoding="utf-8"))

    project_id = fx["project_id"]
    total = fx["total"]
    tasks = fx["tasks"]

    # Patch external calls (no Label Studio, no filesystem CSV output)
    monkeypatch.setattr("domain.results.resolve_project_id", lambda token, project_name: project_id)
    monkeypatch.setattr("domain.results.fetch_tasks_page", lambda token, pid: (tasks, total))

    # If build_results_table decides to reload annotations, we don't want a real HTTP call.
    # Returning [] is fine for a minimal test.
    monkeypatch.setattr("domain.results.fetch_task_annotations", lambda token, task_id: [])

    csv_calls = {"count": 0}

    def _fake_write_csv(columns, rows, pid, pname):
        csv_calls["count"] += 1
        return "dummy.csv"

    monkeypatch.setattr("domain.results._write_results_table_csv", _fake_write_csv)

    # Execute
    out = build_results_table(GetResultsTableCommand(token="dummy", project_name="dummy"))

    # Assert minimal invariants (robust against fixture content changes)
    assert out["total"] == int(total)
    assert out["columns"][:2] == ["task_id", "filename"]
    assert len(out["rows"]) == len(tasks)

    # Every row must have all declared columns (shape/flattening contract)
    for row in out["rows"]:
        for col in out["columns"]:
            assert col in row

    # CSV writer called exactly once
    assert csv_calls["count"] == 1
    assert out["results_output_path_csv"] == "dummy.csv"
