# orchestrator/tests/unit/test_conversion_domain.py
import pytest
from db.models import ConversionJob, File
from domain.conversion import (
    cancel_conversion,
    discard_conversion,
    get_conversion_status,
    handle_conversion_callback,
    prepare_conversion,
    start_conversion,
)
from domain.errors import AlreadyExists, InvalidState, NotFound
from domain.models.conversion import (
    CancelConversionCommand,
    ConversionCallbackCommand,
    ConversionStatusCommand,
    ConvertCommand,
    DiscardConversionCommand,
    PrepareConversionCommand,
)

from tests.unit.fakes.conversion_fakes import (
    FakeConversionRepo,
    FakeProjectRepo,
    FakeQueue,
    FakeStorage,
)


def test_prepare_conversion_creates_project_files_and_job():
    repo = FakeConversionRepo()
    storage = FakeStorage()
    cmd = PrepareConversionCommand(project="my-project", filenames=["a.pdf", "b.pdf"])

    result = prepare_conversion(cmd, storage=storage, repo=repo)

    assert set(repo.projects.keys()) == {"my-project"}
    assert storage.bucket_ensured is True
    assert [f.filename for f in repo.files] == ["a.pdf", "b.pdf"]
    assert repo.conversion_jobs[1].project == "my-project"
    assert repo.conversion_jobs[1].total_files == 2
    assert result["job_id"] == 1
    assert result["presigned_urls"] == [
        {
            "filename": "a.pdf",
            "upload_url": "https://fake-minio/my-project/pdfs/a.pdf",
            "pdf_key": "my-project/pdfs/a.pdf",
        },
        {
            "filename": "b.pdf",
            "upload_url": "https://fake-minio/my-project/pdfs/b.pdf",
            "pdf_key": "my-project/pdfs/b.pdf",
        },
    ]


def test_prepare_conversion_rejects_existing_project():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    storage = FakeStorage()
    cmd = PrepareConversionCommand(project="my-project", filenames=["a.pdf"])

    with pytest.raises(AlreadyExists):
        prepare_conversion(cmd, storage=storage, repo=repo)

    assert repo.files == []
    assert repo.conversion_jobs == {}


def test_start_conversion_transitions_pending_job_to_converting_and_queues_it():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.files.append(File(project="my-project", filename="a.pdf", pdf_key="my-project/pdfs/a.pdf"))
    repo.conversion_jobs[1] = ConversionJob(
        id=1, project="my-project", status="pending", total_files=1, converted_files=0
    )
    queue = FakeQueue()
    cmd = ConvertCommand(job_id=1)

    result = start_conversion(cmd, repo=repo, queue=queue)

    assert repo.conversion_jobs[1].status == "converting"
    assert queue.pushed == [
        {"job_id": 1, "project": "my-project", "pdf_keys": ["my-project/pdfs/a.pdf"]}
    ]
    assert result == {"job_id": 1, "status": "converting"}


def test_start_conversion_raises_when_job_not_found():
    repo = FakeConversionRepo()
    queue = FakeQueue()
    cmd = ConvertCommand(job_id=999)

    with pytest.raises(NotFound):
        start_conversion(cmd, repo=repo, queue=queue)

    assert queue.pushed == []


def test_start_conversion_rejects_job_that_is_not_pending():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.conversion_jobs[1] = ConversionJob(
        id=1, project="my-project", status="converting", total_files=1, converted_files=0
    )
    queue = FakeQueue()
    cmd = ConvertCommand(job_id=1)

    with pytest.raises(InvalidState):
        start_conversion(cmd, repo=repo, queue=queue)

    assert queue.pushed == []
    assert repo.conversion_jobs[1].status == "converting"


def test_cancel_conversion_transitions_converting_job_to_cancelled():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.conversion_jobs[1] = ConversionJob(
        id=1, project="my-project", status="converting", total_files=2, converted_files=1
    )
    cmd = CancelConversionCommand(job_id=1)

    result = cancel_conversion(cmd, repo=repo)

    assert repo.conversion_jobs[1].status == "cancelled"
    assert result == {"job_id": 1, "status": "cancelled"}


def test_cancel_conversion_raises_when_job_not_found():
    repo = FakeConversionRepo()
    cmd = CancelConversionCommand(job_id=999)

    with pytest.raises(NotFound):
        cancel_conversion(cmd, repo=repo)


def test_cancel_conversion_rejects_job_that_is_not_converting():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.conversion_jobs[1] = ConversionJob(
        id=1, project="my-project", status="pending", total_files=2, converted_files=0
    )
    cmd = CancelConversionCommand(job_id=1)

    with pytest.raises(InvalidState):
        cancel_conversion(cmd, repo=repo)

    assert repo.conversion_jobs[1].status == "pending"


def test_discard_conversion_deletes_project_cascade_and_storage_prefix():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.files.append(File(project="my-project", filename="a.pdf", pdf_key="my-project/pdfs/a.pdf"))
    repo.conversion_jobs[1] = ConversionJob(
        id=1, project="my-project", status="failed", total_files=1, converted_files=0
    )
    storage = FakeStorage()
    cmd = DiscardConversionCommand(job_id=1)

    result = discard_conversion(cmd, repo=repo, storage=storage)

    assert "my-project" not in repo.projects
    assert repo.files == []
    assert 1 not in repo.conversion_jobs
    assert repo.committed is True
    assert storage.deleted_prefixes == ["my-project"]
    assert result == {"status": "discarded"}


def test_discard_conversion_returns_already_gone_when_job_missing():
    repo = FakeConversionRepo()
    storage = FakeStorage()
    cmd = DiscardConversionCommand(job_id=999)

    result = discard_conversion(cmd, repo=repo, storage=storage)

    assert result == {"status": "already_gone"}
    assert storage.deleted_prefixes == []


def test_discard_conversion_rejects_job_that_is_converting():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.conversion_jobs[1] = ConversionJob(
        id=1, project="my-project", status="converting", total_files=1, converted_files=0
    )
    storage = FakeStorage()
    cmd = DiscardConversionCommand(job_id=1)

    with pytest.raises(InvalidState):
        discard_conversion(cmd, repo=repo, storage=storage)

    assert "my-project" in repo.projects
    assert storage.deleted_prefixes == []


def test_handle_conversion_callback_raises_when_job_not_found():
    repo = FakeConversionRepo()
    project_repo = FakeProjectRepo()
    cmd = ConversionCallbackCommand(job_id=999, filename="a.pdf", html_key="k", success=True)

    with pytest.raises(NotFound):
        handle_conversion_callback(cmd, repo=repo, project_repo=project_repo)


def test_handle_conversion_callback_skips_writes_when_job_already_cancelled():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.files.append(File(project="my-project", filename="a.pdf", pdf_key="my-project/pdfs/a.pdf"))
    repo.conversion_jobs[1] = ConversionJob(
        id=1, project="my-project", status="cancelled", total_files=1, converted_files=0
    )
    project_repo = FakeProjectRepo()
    cmd = ConversionCallbackCommand(job_id=1, filename="a.pdf", html_key="k", success=True)

    result = handle_conversion_callback(cmd, repo=repo, project_repo=project_repo)

    assert result == {"status": "ok", "continue": False}
    assert repo.files[0].html_key is None
    assert repo.conversion_jobs[1].converted_files == 0


def test_handle_conversion_callback_records_failure_and_marks_job_failed():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.files.append(File(project="my-project", filename="a.pdf", pdf_key="my-project/pdfs/a.pdf"))
    repo.conversion_jobs[1] = ConversionJob(
        id=1, project="my-project", status="converting", total_files=2, converted_files=0
    )
    project_repo = FakeProjectRepo()
    cmd = ConversionCallbackCommand(
        job_id=1, filename="a.pdf", html_key="k", success=False, error="Docling timed out"
    )

    result = handle_conversion_callback(cmd, repo=repo, project_repo=project_repo)

    assert repo.files[0].error == "Docling timed out"
    assert repo.conversion_jobs[1].converted_files == 1
    assert repo.conversion_jobs[1].status == "failed"
    assert repo.conversion_jobs[1].error == "a.pdf: Docling timed out"
    assert result == {"status": "ok", "continue": False}


def test_handle_conversion_callback_does_not_overwrite_error_when_job_already_failed():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.files.append(File(project="my-project", filename="b.pdf", pdf_key="my-project/pdfs/b.pdf"))
    repo.conversion_jobs[1] = ConversionJob(
        id=1,
        project="my-project",
        status="failed",
        total_files=2,
        converted_files=1,
        error="a.pdf: boom",
    )
    project_repo = FakeProjectRepo()
    cmd = ConversionCallbackCommand(
        job_id=1, filename="b.pdf", html_key="k", success=False, error="also broken"
    )

    handle_conversion_callback(cmd, repo=repo, project_repo=project_repo)

    assert repo.conversion_jobs[1].error == "a.pdf: boom"


def test_handle_conversion_callback_continues_when_more_files_remain():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.files.append(File(project="my-project", filename="a.pdf", pdf_key="my-project/pdfs/a.pdf"))
    repo.conversion_jobs[1] = ConversionJob(
        id=1, project="my-project", status="converting", total_files=2, converted_files=0
    )
    project_repo = FakeProjectRepo()
    cmd = ConversionCallbackCommand(
        job_id=1,
        filename="a.pdf",
        html_key="html/a.html",
        success=True,
        pdf_hash="p1",
        html_hash="h1",
    )

    result = handle_conversion_callback(cmd, repo=repo, project_repo=project_repo)

    assert repo.files[0].html_key == "html/a.html"
    assert repo.conversion_jobs[1].converted_files == 1
    assert repo.conversion_jobs[1].status == "converting"
    assert project_repo.document_set_hashes_set == []
    assert result == {"status": "ok", "continue": True}


def test_handle_conversion_callback_completes_job_and_sets_document_set_hash():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.files.append(File(project="my-project", filename="a.pdf", pdf_key="my-project/pdfs/a.pdf"))
    repo.conversion_jobs[1] = ConversionJob(
        id=1, project="my-project", status="converting", total_files=1, converted_files=0
    )
    project_repo = FakeProjectRepo()
    cmd = ConversionCallbackCommand(
        job_id=1, filename="a.pdf", html_key="html/a.html", success=True
    )

    result = handle_conversion_callback(cmd, repo=repo, project_repo=project_repo)

    assert repo.conversion_jobs[1].status == "done"
    assert project_repo.document_set_hashes_set == ["my-project"]
    assert result == {"status": "ok", "continue": False}


def test_handle_conversion_callback_stops_when_status_flipped_to_cancelled_mid_flight():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.files.append(File(project="my-project", filename="a.pdf", pdf_key="my-project/pdfs/a.pdf"))
    repo.conversion_jobs[1] = ConversionJob(
        id=1, project="my-project", status="converting", total_files=2, converted_files=0
    )
    project_repo = FakeProjectRepo()
    cmd = ConversionCallbackCommand(
        job_id=1, filename="a.pdf", html_key="html/a.html", success=True
    )

    original_increment = repo.increment_converted_files

    def increment_then_cancel(job_id):
        original_increment(job_id)
        repo.conversion_jobs[job_id].status = "cancelled"

    repo.increment_converted_files = increment_then_cancel

    result = handle_conversion_callback(cmd, repo=repo, project_repo=project_repo)

    assert result == {"status": "ok", "continue": False}
    assert project_repo.document_set_hashes_set == []


def test_get_conversion_status_returns_job_details():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.conversion_jobs[1] = ConversionJob(
        id=1,
        project="my-project",
        status="converting",
        total_files=3,
        converted_files=1,
        error=None,
    )
    cmd = ConversionStatusCommand(job_id=1)

    result = get_conversion_status(cmd, repo=repo)

    assert result == {
        "job_id": 1,
        "status": "converting",
        "total_files": 3,
        "converted_files": 1,
        "error": None,
    }


def test_get_conversion_status_raises_when_job_not_found():
    repo = FakeConversionRepo()
    cmd = ConversionStatusCommand(job_id=999)

    with pytest.raises(NotFound):
        get_conversion_status(cmd, repo=repo)
