# orchestrator/domain/conversion.py

import json
import os
from datetime import timedelta

import redis
from db.models import ConversionJob, File, Project
from minio import Minio
from minio.error import S3Error
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domain.errors import AlreadyExists, ExternalServiceError, InvalidState, NotFound
from domain.models.conversion import (
    ConversionCallbackCommand,
    ConversionStatusCommand,
    ConvertCommand,
    PrepareConversionCommand,
)

MINIO_ENDPOINT = (
    os.getenv("MINIO_CONTAINER_NAME", "minio") + ":" + os.getenv("MINIO_API_PORT", "9000")
)
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "yourpassword")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "xtractyl")
MINIO_PRESIGN_EXPIRY = int(os.getenv("MINIO_PRESIGN_EXPIRY_SECONDS", "3600"))
REDIS_HOST = os.getenv("REDIS_HOST", "job_queue")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CONVERSION_QUEUE = "conversion_jobs"
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def _minio_client() -> Minio:
    return Minio(
        MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False
    )


def _redis_client() -> redis.Redis:
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=1)


def prepare_conversion(cmd: PrepareConversionCommand) -> dict:
    db = SessionLocal()
    try:
        if db.query(Project).filter(Project.name == cmd.project).first():
            raise AlreadyExists(
                code="PROJECT_ALREADY_EXISTS", message="A project with this name already exists."
            )

        project = Project(name=cmd.project, questions_and_labels={})
        db.add(project)
        db.flush()

        minio = _minio_client()
        try:
            if not minio.bucket_exists(MINIO_BUCKET):
                minio.make_bucket(MINIO_BUCKET)
        except S3Error as e:
            raise ExternalServiceError(
                code="MINIO_UNAVAILABLE", message="Could not connect to MinIO."
            ) from e

        presigned_urls = []
        for filename in cmd.filenames:
            pdf_key = f"{cmd.project}/pdfs/{filename}"
            db.add(File(project=cmd.project, filename=filename, pdf_key=pdf_key))
            try:
                url = minio.presigned_put_object(
                    MINIO_BUCKET, pdf_key, expires=timedelta(seconds=MINIO_PRESIGN_EXPIRY)
                )
            except S3Error as e:
                raise ExternalServiceError(
                    code="MINIO_PRESIGN_FAILED",
                    message=f"Could not generate presigned URL for {filename}.",
                ) from e
            presigned_urls.append({"filename": filename, "upload_url": url, "pdf_key": pdf_key})

        job = ConversionJob(
            project=cmd.project, status="pending", total_files=len(cmd.filenames), converted_files=0
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return {"job_id": job.id, "presigned_urls": presigned_urls}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def start_conversion(cmd: ConvertCommand) -> dict:
    db = SessionLocal()
    try:
        job = db.query(ConversionJob).filter(ConversionJob.id == cmd.job_id).first()
        if not job:
            raise NotFound(code="CONVERSION_JOB_NOT_FOUND", message="Conversion job not found.")
        if job.status != "pending":
            raise InvalidState(
                code="JOB_NOT_PENDING", message=f"Job is already in state '{job.status}'."
            )

        files = db.query(File).filter(File.project == job.project).all()
        pdf_keys = [f.pdf_key for f in files if f.pdf_key]

        _redis_client().rpush(
            CONVERSION_QUEUE,
            json.dumps(
                {
                    "job_id": job.id,
                    "project": job.project,
                    "pdf_keys": pdf_keys,
                    "minio_bucket": MINIO_BUCKET,
                }
            ),
        )
        job.status = "converting"
        db.commit()
        return {"job_id": job.id, "status": "converting"}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_conversion_status(cmd: ConversionStatusCommand) -> dict:
    db = SessionLocal()
    try:
        job = db.query(ConversionJob).filter(ConversionJob.id == cmd.job_id).first()
        if not job:
            raise NotFound(code="CONVERSION_JOB_NOT_FOUND", message="Conversion job not found.")
        return {
            "job_id": job.id,
            "status": job.status,
            "total_files": job.total_files,
            "converted_files": job.converted_files,
            "error": job.error,
        }
    finally:
        db.close()


def handle_conversion_callback(cmd: ConversionCallbackCommand) -> dict:
    db = SessionLocal()
    try:
        job = db.query(ConversionJob).filter(ConversionJob.id == cmd.job_id).first()
        if not job:
            raise NotFound(code="CONVERSION_JOB_NOT_FOUND", message="Conversion job not found.")

        if cmd.success:
            file_record = (
                db.query(File)
                .filter(File.project == job.project, File.filename == cmd.filename)
                .first()
            )
            if file_record:
                file_record.html_key = cmd.html_key

        job.converted_files += 1

        if job.converted_files >= job.total_files:
            failed = (
                db.query(File).filter(File.project == job.project, File.html_key.is_(None)).count()
            )
            job.status = "failed" if failed > 0 else "done"
            if failed > 0:
                job.error = f"{failed} file(s) failed to convert."

        db.commit()
        return {"status": "ok"}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
