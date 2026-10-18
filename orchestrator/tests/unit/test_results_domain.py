# orchestrator/tests/unit/test_results_domain.py  (neu)
import pytest
from api.contracts.results import GetResultsTableResponse, ListProjectsReadyForResultsResponse
from domain.errors import InternalError, InvalidState, NotFound
from domain.models.results import GetResultsTableCommand
from domain.results import build_results_table, list_projects_ready_for_results

from tests.unit.fakes.builders import make_run, make_task
from tests.unit.fakes.prelabelling_run_repository import FakePrelabellingRunRepo


def make_command(project_name="proj"):
    return GetResultsTableCommand(project_name=project_name)


def make_done_repo(tasks, run_id=1):
    return FakePrelabellingRunRepo(
        existing_run=make_run("done", run_id=run_id),
        successful_tasks=tasks,
    )


def test_list_projects_ready_for_results_returns_projects_from_repo():
    repo = FakePrelabellingRunRepo(ready_projects=["a", "b"])

    assert list_projects_ready_for_results(run_repo=repo) == {"projects": ["a", "b"]}


def test_build_results_table_without_run_raises_not_found():
    repo = FakePrelabellingRunRepo(existing_run=None)

    with pytest.raises(NotFound) as exc:
        build_results_table(make_command("proj"), run_repo=repo)

    assert exc.value.code == "RUN_NOT_FOUND"
    assert "proj" in exc.value.message


@pytest.mark.parametrize("status", ["pending", "running", "failed", "cancelled", "incomplete"])
def test_build_results_table_for_run_that_is_not_done_raises_invalid_state(status):
    repo = FakePrelabellingRunRepo(existing_run=make_run(status))

    with pytest.raises(InvalidState) as exc:
        build_results_table(make_command(), run_repo=repo)

    assert exc.value.code == "RUN_NOT_DONE"
    assert status in exc.value.message
    assert repo.successful_tasks_requested == []


def test_build_results_table_for_done_run_without_tasks_raises_internal_error():
    repo = make_done_repo(tasks=[])

    with pytest.raises(InternalError) as exc:
        build_results_table(make_command(), run_repo=repo)

    assert exc.value.code == "DONE_RUN_WITHOUT_TASKS"
    assert "proj" in exc.value.message


def test_build_results_table_reads_the_tasks_of_the_run():
    repo = make_done_repo(tasks=[make_task("a.html", 101, {"name": {"answer": "Alice"}})], run_id=7)

    build_results_table(make_command(), run_repo=repo)

    assert repo.successful_tasks_requested == [7]


def test_build_results_table_builds_columns_and_rows_from_the_llm_answers():
    tasks = [
        make_task(
            "a.html",
            101,
            {"name": {"answer": "Alice"}, "date": {"answer": "2020"}},
            task_id=1,
        ),
        make_task(
            "b.html",
            102,
            {"name": {"answer": "Bob"}, "city": {"answer": "Berlin"}},
            task_id=2,
        ),
    ]

    result = build_results_table(make_command(), run_repo=make_done_repo(tasks))

    # fixed columns first, then every label once, in order of first appearance
    assert result["columns"] == ["task_id", "filename", "name__pred", "date__pred", "city__pred"]
    assert result["rows"] == [
        {"task_id": 101, "filename": "a.html", "name__pred": "Alice", "date__pred": "2020"},
        # a label the task does not have is simply missing from its row
        {"task_id": 102, "filename": "b.html", "name__pred": "Bob", "city__pred": "Berlin"},
    ]
    assert result["total"] == 2


def test_build_results_table_uses_empty_string_for_answers_without_a_usable_answer():
    tasks = [make_task("a.html", 101, {"name": "unexpected", "date": {"confidence": 1}})]

    result = build_results_table(make_command(), run_repo=make_done_repo(tasks))

    assert result["rows"] == [
        {"task_id": 101, "filename": "a.html", "name__pred": "", "date__pred": ""}
    ]


def test_build_results_table_handles_tasks_without_llm_answers():
    tasks = [
        make_task("a.html", 101, raw_llm_answers=None, task_id=1),
        make_task("b.html", 102, raw_llm_answers={}, task_id=2),
    ]

    result = build_results_table(make_command(), run_repo=make_done_repo(tasks))

    assert result["columns"] == ["task_id", "filename"]
    assert result["rows"] == [
        {"task_id": 101, "filename": "a.html"},
        {"task_id": 102, "filename": "b.html"},
    ]
    assert result["total"] == 2


def test_domain_results_satisfy_the_api_response_contracts():
    tasks = [make_task("a.html", 101, {"name": {"answer": "Alice"}})]
    repo = FakePrelabellingRunRepo(
        existing_run=make_run("done"),
        successful_tasks=tasks,
        ready_projects=["proj"],
    )

    table = build_results_table(make_command(), run_repo=repo)
    projects = list_projects_ready_for_results(run_repo=repo)

    GetResultsTableResponse.model_validate(table)
    ListProjectsReadyForResultsResponse.model_validate(projects)
