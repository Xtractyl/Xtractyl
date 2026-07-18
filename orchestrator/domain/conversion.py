# orchestrator/domain/conversion.py


from infrastructure.interfaces.queue import QueueInterface
from infrastructure.interfaces.repository import ConversionRepositoryInterface
from infrastructure.interfaces.storage import StorageInterface

from domain.errors import AlreadyExists, InvalidState, NotFound
from domain.models.conversion import (
    ConversionCallbackCommand,
    ConversionStatusCommand,
    ConvertCommand,
    DiscardConversionCommand,
    PrepareConversionCommand,
)


def prepare_conversion(
    cmd: PrepareConversionCommand, storage: StorageInterface, repo: ConversionRepositoryInterface
) -> dict:
    if repo.project_exists(cmd.project):
        raise AlreadyExists(
            code="PROJECT_ALREADY_EXISTS",
            message="A project with this name already exists.",
        )
    repo.create_project(cmd.project)
    storage.ensure_bucket()
    presigned_urls = []
    for filename in cmd.filenames:
        pdf_key = f"{cmd.project}/pdfs/{filename}"
        repo.create_file(project=cmd.project, filename=filename, pdf_key=pdf_key)
        url = storage.presigned_put(pdf_key)
        presigned_urls.append({"filename": filename, "upload_url": url, "pdf_key": pdf_key})
    job_id = repo.create_conversion_job(project=cmd.project, total_files=len(cmd.filenames))
    return {"job_id": job_id, "presigned_urls": presigned_urls}


def discard_conversion(
    cmd: DiscardConversionCommand,
    repo: ConversionRepositoryInterface,
    storage: StorageInterface,
) -> dict:
    job = repo.get_conversion_job(cmd.job_id)
    if not job:
        return {"status": "already_gone"}
    if job.status not in ("pending", "failed"):
        raise InvalidState(
            code="JOB_NOT_DISCARDABLE",
            message="Job has already started converting; cannot discard.",
        )
    storage.delete_prefix(job.project)
    repo.delete_project_cascade(job.project)
    return {"status": "discarded"}


def start_conversion(
    cmd: ConvertCommand, repo: ConversionRepositoryInterface, queue: QueueInterface
) -> dict:
    job = repo.get_conversion_job(cmd.job_id)
    if not job:
        raise NotFound(code="CONVERSION_JOB_NOT_FOUND", message="Conversion job not found.")
    if job.status != "pending":
        raise InvalidState(
            code="JOB_NOT_PENDING", message=f"Job is already in state '{job.status}'."
        )
    pdf_keys = repo.get_pdf_keys_for_project(job.project)
    queue.push_conversion_job(
        job_id=job.id,
        project=job.project,
        pdf_keys=pdf_keys,
    )
    repo.set_conversion_job_status(job.id, "converting")
    return {"job_id": job.id, "status": "converting"}


def get_conversion_status(
    cmd: ConversionStatusCommand, repo: ConversionRepositoryInterface
) -> dict:
    job = repo.get_conversion_job(cmd.job_id)
    if not job:
        raise NotFound(code="CONVERSION_JOB_NOT_FOUND", message="Conversion job not found.")
    return {
        "job_id": job.id,
        "status": job.status,
        "total_files": job.total_files,
        "converted_files": job.converted_files,
        "error": job.error,
    }


def handle_conversion_callback(
    cmd: ConversionCallbackCommand, repo: ConversionRepositoryInterface
) -> dict:
    job = repo.get_conversion_job(cmd.job_id)
    if not job:
        raise NotFound(code="CONVERSION_JOB_NOT_FOUND", message="Conversion job not found.")
    if not cmd.success:
        repo.set_file_error(
            project=job.project,
            filename=cmd.filename,
            error=cmd.error or "Conversion failed for unknown reason.",
        )
        repo.increment_converted_files(job.id)
        if job.status != "failed":
            repo.set_conversion_job_status(
                job.id,
                "failed",
                error=f"{cmd.filename}: {cmd.error or 'conversion failed'}",
            )
        return {"status": "ok", "continue": False}

    repo.set_file_html_key(
        project=job.project,
        filename=cmd.filename,
        html_key=cmd.html_key,
        pdf_hash=cmd.pdf_hash,
        html_hash=cmd.html_hash,
    )
    repo.increment_converted_files(job.id)
    updated_job = repo.get_conversion_job(cmd.job_id)
    if updated_job.status == "failed":
        # Unreachable under the current strictly sequential single-worker processing
        # (fail-fast breaks the per-file loop immediately). Kept as a guard for a
        # future intra-job parallelization where this race could actually occur.
        return {"status": "ok", "continue": False}

    if updated_job.converted_files >= updated_job.total_files:
        repo.set_conversion_job_status(job.id, "done")
        return {"status": "ok", "continue": False}

    return {"status": "ok", "continue": True}
