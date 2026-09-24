# worker_conversion/domain.py
from __future__ import annotations

import hashlib
import os

from config import MINIO_BUCKET
from contracts import ConversionJobPayload
from infrastructure.errors import DoclingError, StorageError
from infrastructure.interfaces.callback import CallbackClientInterface
from infrastructure.interfaces.docling import DoclingClientInterface
from infrastructure.interfaces.storage import ConversionStorageInterface
from utils.logging_utils import dev_logger, safe_logger


def convert_file(
    job_id: int,
    pdf_key: str,
    storage: ConversionStorageInterface,
    docling: DoclingClientInterface,
) -> tuple[str, str, str]:
    """Returns (html_key, pdf_hash, html_hash). Raises StorageError or DoclingError on failure."""
    filename = os.path.basename(pdf_key)
    html_key = pdf_key.replace("/pdfs/", "/htmls/").replace(".pdf", ".html")

    pdf_bytes = storage.get_object(MINIO_BUCKET, pdf_key)
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    html_content = docling.convert(filename, pdf_bytes)
    html_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()

    html_bytes = html_content.encode("utf-8")
    storage.put_object(MINIO_BUCKET, html_key, html_bytes, "text/html")

    return html_key, pdf_hash, html_hash


def handle_job(
    job: ConversionJobPayload,
    storage: ConversionStorageInterface,
    docling: DoclingClientInterface,
    callback: CallbackClientInterface,
) -> None:
    safe_logger.info("conversion_job_started | job_id=%s", job.job_id)
    for pdf_key in job.pdf_keys:
        filename = os.path.basename(pdf_key)
        try:
            html_key, pdf_hash, html_hash = convert_file(job.job_id, pdf_key, storage, docling)
            success, error = True, None
        except (StorageError, DoclingError) as e:
            html_key, pdf_hash, html_hash = None, None, None
            success, error = False, str(e)

        should_continue = callback.send(
            job_id=job.job_id,
            filename=filename,
            html_key=html_key,
            success=success,
            error=error,
            pdf_hash=pdf_hash,
            html_hash=html_hash,
        )
        if not success:
            safe_logger.error(
                "file_conversion_failed | job_id=%s | pdf_filename=%s", job.job_id, filename
            )
            if dev_logger:
                dev_logger.error(
                    "file_conversion_failed_dev | job_id=%s | pdf_filename=%s | error=%s",
                    job.job_id,
                    filename,
                    error,
                )
        if not should_continue:
            safe_logger.info("conversion_job_stopped_early | job_id=%s", job.job_id)
            break

    safe_logger.info("conversion_job_finished | job_id=%s", job.job_id)
