# orchestrator/tests/unit/test_conversion_domain.py
import pytest
from domain.conversion import prepare_conversion
from domain.errors import AlreadyExists
from domain.models.conversion import PrepareConversionCommand

from tests.unit.fakes.conversion_fakes import FakeConversionRepo, FakeStorage


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
