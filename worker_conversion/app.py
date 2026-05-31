# worker_conversion/app.py
from __future__ import annotations

import io
import json
import os
from datetime import timedelta

import redis
import requests
from minio import Minio
from minio.error import S3Error
from pydantic import BaseModel, ValidationError
from utils.logging_utils import dev_logger, safe_logger

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "job_queue"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=1,
    decode_responses=True,
)
QUEUE = "conversion_jobs"

MINIO_ENDPOINT = (
    os.getenv("MINIO_CONTAINER_NAME", "minio") + ":" + os.getenv("MINIO_API_PORT", "9000")
)
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "yourpassword")

DOCLING_URL = (
    f"http://{os.getenv('DOCLING_CONTAINER_NAME', 'docling')}:{os.getenv('DOCLING_PORT', '5004')}"
)
ORCHESTRATOR_CALLBACK_URL = f"http://{os.getenv('ORCH_CONTAINER_NAME', 'orchestrator')}:{os.getenv('ORCH_PORT', '5001')}/conversion/callback"

MINIO_BUCKET = os.getenv("MINIO_BUCKET", "xtractyl")


class ConversionJobPayload(BaseModel):
    job_id: int
    project: str
    pdf_keys: list[str]


def _minio_client() -> Minio:
    return Minio(
        MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False
    )


def _send_callback(
    job_id: int, filename: str, html_key: str | None, success: bool, error: str | None = None
) -> None:
    try:
        requests.post(
            ORCHESTRATOR_CALLBACK_URL,
            json={
                "job_id": job_id,
                "filename": filename,
                "html_key": html_key or "",
                "success": success,
                "error": error,
            },
            timeout=10,
        )
    except requests.RequestException as e:
        safe_logger.error("callback_failed | job_id=%s | pdf_filename=%s", job_id, filename)
        if dev_logger:
            dev_logger.exception("callback_failed_dev | error=%s", str(e))


def convert_file(job_id: int, pdf_key: str) -> tuple[bool, str | None, str | None]:
    filename = os.path.basename(pdf_key)
    html_key = pdf_key.replace("/pdfs/", "/htmls/").replace(".pdf", ".html")
    minio = _minio_client()

    try:
        pdf_url = minio.presigned_get_object(MINIO_BUCKET, pdf_key, expires=timedelta(minutes=30))
    except S3Error as e:
        return False, None, f"Could not generate presigned URL: {e}"

    try:
        response = requests.post(
            f"{DOCLING_URL}/convert", json={"pdf_url": pdf_url, "filename": filename}, timeout=300
        )
        response.raise_for_status()
        html_content = response.json().get("html")
        if not html_content:
            return False, None, "Docling returned no HTML content."
    except requests.RequestException as e:
        return False, None, f"Docling conversion failed: {e}"

    try:
        html_bytes = html_content.encode("utf-8")
        minio.put_object(
            MINIO_BUCKET,
            html_key,
            io.BytesIO(html_bytes),
            length=len(html_bytes),
            content_type="text/html",
        )
    except S3Error as e:
        return False, None, f"Could not upload HTML to MinIO: {e}"

    return True, html_key, None


def handle_job(job: ConversionJobPayload) -> None:
    safe_logger.info("conversion_job_started | job_id=%s", job.job_id)
    for pdf_key in job.pdf_keys:
        filename = os.path.basename(pdf_key)
        success, html_key, error = convert_file(job.job_id, pdf_key)
        _send_callback(
            job_id=job.job_id, filename=filename, html_key=html_key, success=success, error=error
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

    safe_logger.info("conversion_job_finished | job_id=%s", job.job_id)


def main() -> None:
    safe_logger.info("worker_conversion_starting")
    while True:
        item = r.blpop(QUEUE, timeout=5)
        if not item:
            continue
        _, raw = item
        try:
            job = ConversionJobPayload.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            safe_logger.error("invalid_conversion_payload | error=%s", str(e))
            if dev_logger:
                dev_logger.exception("invalid_conversion_payload_dev | error=%s", str(e))
            continue
        try:
            handle_job(job)
        except Exception as e:
            safe_logger.error(
                "conversion_job_crashed | job_id=%s", getattr(job, "job_id", "unknown")
            )
            if dev_logger:
                dev_logger.exception(
                    "conversion_job_crashed_dev | job_id=%s | error=%s",
                    getattr(job, "job_id", "unknown"),
                    str(e),
                )


if __name__ == "__main__":
    main()
