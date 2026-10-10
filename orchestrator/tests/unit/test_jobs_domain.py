# /orchestrator/tests/unit/test_jobs_domain.py
import pytest
from db.models import Model
from domain.errors import AlreadyExists, InvalidState, NotFound
from domain.jobs import enqueue_prelabel_job
from domain.models.jobs import EnqueueJobCommand

from tests.unit.fakes.builders import make_run
from tests.unit.fakes.model_repository import FakeModelRepo
from tests.unit.fakes.prelabelling_run_repository import FakePrelabellingRunRepo
from tests.unit.fakes.project_repository import FakeProjectRepo
from tests.unit.fakes.queue import FakePrelabelQueue

QUESTIONS_AND_LABELS = {"questions": ["q1"], "labels": ["l1"]}


def make_model(model_id, archived_name):
    return Model(id=model_id, archived_name=archived_name)


def make_command(**overrides):
    values = {
        "project_name": "proj",
        "model": "llama3",
        "system_prompt": "Extract.",
        "token": "tok",
    }
    values.update(overrides)
    return EnqueueJobCommand(**values)


def make_project_repo(**overrides):
    values = {
        "label_studio_ids": {"proj": 7},
        "questions_and_labels": {"proj": QUESTIONS_AND_LABELS},
        "tasks_uploaded": ["proj"],
        "html_keys": {"proj": ["proj/html/a.html", "proj/html/b.html"]},
    }
    values.update(overrides)
    return FakeProjectRepo(**values)


def make_model_repo():
    return FakeModelRepo([make_model(1, "llama3"), make_model(2, "gemma")])


def test_enqueue_new_run_creates_run_and_tasks_and_pushes_payload():
    run_repo = FakePrelabellingRunRepo(new_run_id=5, pending_filenames=["a.html", "b.html"])
    queue = FakePrelabelQueue()

    result = enqueue_prelabel_job(
        make_command(),
        run_repo=run_repo,
        project_repo=make_project_repo(),
        model_repo=make_model_repo(),
        queue=queue,
    )

    assert run_repo.created_runs == [("proj", 1, "Extract.")]
    assert run_repo.created_tasks == [(5, ["a.html", "b.html"])]
    assert run_repo.resumed == []
    assert queue.pushed == [
        {
            "job_id": "5",
            "project_name": "proj",
            "label_studio_id": 7,
            "model": "llama3",
            "system_prompt": "Extract.",
            "questions_and_labels": QUESTIONS_AND_LABELS,
            "token": "tok",
            "task_filenames": ["a.html", "b.html"],
        }
    ]
    assert result == {
        "job_id": "5",
        "status_url": "/prelabel/status/5",
        "cancel_url": "/prelabel/cancel/5",
    }


@pytest.mark.parametrize(
    "project_repo, expected_error, expected_code",
    [
        (make_project_repo(label_studio_ids={}), NotFound, "PROJECT_NOT_FOUND"),
        (make_project_repo(questions_and_labels={}), NotFound, "QAL_NOT_FOUND"),
        (make_project_repo(tasks_uploaded=[]), InvalidState, "TASKS_NOT_UPLOADED"),
    ],
    ids=["no_label_studio_id", "no_questions_and_labels", "tasks_not_uploaded"],
)
def test_enqueue_rejects_project_that_is_not_ready(project_repo, expected_error, expected_code):
    run_repo = FakePrelabellingRunRepo()
    queue = FakePrelabelQueue()

    with pytest.raises(expected_error) as excinfo:
        enqueue_prelabel_job(
            make_command(),
            run_repo=run_repo,
            project_repo=project_repo,
            model_repo=make_model_repo(),
            queue=queue,
        )

    assert excinfo.value.code == expected_code
    assert run_repo.created_runs == []
    assert queue.pushed == []


def test_enqueue_rejects_unknown_model():
    run_repo = FakePrelabellingRunRepo()
    queue = FakePrelabelQueue()

    with pytest.raises(NotFound) as excinfo:
        enqueue_prelabel_job(
            make_command(model="unknown"),
            run_repo=run_repo,
            project_repo=make_project_repo(),
            model_repo=make_model_repo(),
            queue=queue,
        )

    assert excinfo.value.code == "MODEL_NOT_FOUND"
    assert run_repo.created_runs == []


@pytest.mark.parametrize("status", ["pending", "running", "done"])
def test_enqueue_rejects_project_with_blocking_run(status):
    run_repo = FakePrelabellingRunRepo(existing_run=make_run(status))
    queue = FakePrelabelQueue()

    with pytest.raises(AlreadyExists) as excinfo:
        enqueue_prelabel_job(
            make_command(),
            run_repo=run_repo,
            project_repo=make_project_repo(),
            model_repo=make_model_repo(),
            queue=queue,
        )

    assert excinfo.value.code == "PRELABELLING_RUN_ALREADY_EXISTS"
    assert run_repo.created_runs == []
    assert run_repo.resumed == []
    assert queue.pushed == []


@pytest.mark.parametrize("status", ["failed", "cancelled", "incomplete"])
def test_enqueue_resumes_existing_run_with_unchanged_configuration(status):
    run_repo = FakePrelabellingRunRepo(
        existing_run=make_run(status, run_id=3), pending_filenames=["b.html"]
    )
    queue = FakePrelabelQueue()

    result = enqueue_prelabel_job(
        make_command(),
        run_repo=run_repo,
        project_repo=make_project_repo(),
        model_repo=make_model_repo(),
        queue=queue,
    )

    assert run_repo.resumed == [3]
    assert run_repo.created_runs == []
    assert run_repo.created_tasks == []
    assert len(queue.pushed) == 1
    assert queue.pushed[0]["job_id"] == "3"
    assert queue.pushed[0]["task_filenames"] == ["b.html"]
    assert result["job_id"] == "3"


def test_enqueue_resumes_when_system_prompt_differs_only_in_surrounding_whitespace():
    run_repo = FakePrelabellingRunRepo(
        existing_run=make_run("failed", system_prompt="Extract."), pending_filenames=["b.html"]
    )
    queue = FakePrelabelQueue()

    enqueue_prelabel_job(
        make_command(system_prompt="  Extract.\n"),
        run_repo=run_repo,
        project_repo=make_project_repo(),
        model_repo=make_model_repo(),
        queue=queue,
    )

    assert run_repo.resumed == [1]
    assert len(queue.pushed) == 1


@pytest.mark.parametrize(
    "run_model_id, run_prompt",
    [(2, "Extract."), (1, "Other prompt.")],
    ids=["different_model", "different_system_prompt"],
)
def test_enqueue_rejects_resume_with_changed_configuration(run_model_id, run_prompt):
    run_repo = FakePrelabellingRunRepo(
        existing_run=make_run("failed", model_id=run_model_id, system_prompt=run_prompt)
    )
    queue = FakePrelabelQueue()

    with pytest.raises(InvalidState) as excinfo:
        enqueue_prelabel_job(
            make_command(),
            run_repo=run_repo,
            project_repo=make_project_repo(),
            model_repo=make_model_repo(),
            queue=queue,
        )

    assert excinfo.value.code == "RESUME_CONFIG_MISMATCH"
    assert run_repo.resumed == []
    assert run_repo.created_runs == []
    assert queue.pushed == []


def test_enqueue_rejects_resume_that_lost_the_race():
    run_repo = FakePrelabellingRunRepo(existing_run=make_run("failed"), resume_succeeds=False)
    queue = FakePrelabelQueue()

    with pytest.raises(AlreadyExists) as excinfo:
        enqueue_prelabel_job(
            make_command(),
            run_repo=run_repo,
            project_repo=make_project_repo(),
            model_repo=make_model_repo(),
            queue=queue,
        )

    assert excinfo.value.code == "PRELABELLING_RUN_ALREADY_EXISTS"
    assert queue.pushed == []


def test_enqueue_translates_concurrent_first_start_into_already_exists():
    run_repo = FakePrelabellingRunRepo(create_raises_integrity_error=True)
    queue = FakePrelabelQueue()

    with pytest.raises(AlreadyExists) as excinfo:
        enqueue_prelabel_job(
            make_command(),
            run_repo=run_repo,
            project_repo=make_project_repo(),
            model_repo=make_model_repo(),
            queue=queue,
        )

    assert excinfo.value.code == "PRELABELLING_RUN_ALREADY_EXISTS"
    assert queue.pushed == []


def test_enqueue_rejects_run_without_pending_tasks():
    run_repo = FakePrelabellingRunRepo(new_run_id=5, pending_filenames=[])
    queue = FakePrelabelQueue()

    with pytest.raises(NotFound) as excinfo:
        enqueue_prelabel_job(
            make_command(),
            run_repo=run_repo,
            project_repo=make_project_repo(html_keys={"proj": []}),
            model_repo=make_model_repo(),
            queue=queue,
        )

    assert excinfo.value.code == "PENDING_TASKS_NOT_FOUND"
    assert run_repo.created_tasks == [(5, [])]
    assert queue.pushed == []
