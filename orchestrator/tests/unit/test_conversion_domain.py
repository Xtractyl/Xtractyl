# orchestrator/tests/unit/test_conversion_domain.py
import pytest
from db.models import ConversionJob, File
from domain.conversion import (
    cancel_conversion,
    discard_conversion,
    handle_conversion_callback,
    prepare_conversion,
    start_conversion,
)
from domain.errors import AlreadyExists, InvalidState, NotFound
from domain.models.conversion import (
    CancelConversionCommand,
    ConversionCallbackCommand,
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
    assert repo.jobs[1].project == "my-project"
    assert repo.jobs[1].total_files == 2
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
    assert repo.jobs == {}



def test_start_conversion_transitions_pending_job_to_converting_and_queues_it():
    repo = FakeConversionRepo(existing_projects={"my-project"})
    repo.files.append(File(project="my-project", filename="a.pdf", pdf_key="my-project/pdfs/a.pdf"))
    repo.jobs[1] = ConversionJob(
        id=1, project="my-project", status="pending", total_files=1, converted_files=0
    )
    queue = FakeQueue()
    cmd = ConvertCommand(job_id=1)

    result = start_conversion(cmd, repo=repo, queue=queue)

    assert repo.jobs[1].status == "converting"
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
    repo.jobs[1] = ConversionJob(
        id=1, project="my-project", status="converting", total_files=1, converted_files=0
    )
    queue = FakeQueue()
    cmd = ConvertCommand(job_id=1)

    with pytest.raises(InvalidState):
        start_conversion(cmd, repo=repo, queue=queue)

    assert queue.pushed == []
    assert repo.jobs[1].status == "converting"

