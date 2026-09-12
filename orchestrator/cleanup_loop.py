# orchestrator/cleanup_loop.py
import os
import time

from domain.cleanup import (
    cleanup_stale_conversion_jobs,
    sweep_orphaned_label_studio_projects,
    sweep_orphaned_storage_prefixes,
    sweep_unarchived_ollama_models,
)
from infrastructure.label_studio.label_studio_client import LabelStudioClient
from infrastructure.ollama.ollama_client import OllamaClient
from infrastructure.storage.minio_storage import MinioStorage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.logging_utils import dev_logger, safe_logger

INTERVAL = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "3600"))
STALE_HOURS = int(os.getenv("CLEANUP_STALE_AFTER_HOURS", "2"))
LABEL_STUDIO_USER_TOKEN = os.getenv("LABEL_STUDIO_USER_TOKEN", "")
ARCHIVE_PREFIX = os.getenv("XTRACTYL_MODEL_ARCHIVE_PREFIX", "xtractyl-archive")


DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_XTRACTYL_USER', 'xtractyl')}:"
    f"{os.getenv('POSTGRES_XTRACTYL_PASSWORD', 'yourpassword')}@"
    f"{os.getenv('POSTGRES_XTRACTYL_CONTAINER_NAME', 'postgres_xtractyl')}:5432/"
    f"{os.getenv('POSTGRES_XTRACTYL_DB', 'xtractyl')}"
)
engine = create_engine(DATABASE_URL)
session_factory = sessionmaker(bind=engine)

label_studio = LabelStudioClient()
ollama_client = OllamaClient(base_url=os.getenv("OLLAMA_BASE", "http://ollama:11434"))


storage = MinioStorage(
    endpoint=os.getenv("MINIO_CONTAINER_NAME", "minio") + ":" + os.getenv("MINIO_API_PORT", "9000"),
    access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD", "yourpassword"),
    bucket=os.getenv("MINIO_BUCKET", "xtractyl"),
    presign_expiry_seconds=0,
)


def main():
    safe_logger.info("cleanup_service_starting")
    while True:
        db = session_factory()
        try:
            n = cleanup_stale_conversion_jobs(db, storage, STALE_HOURS)
            if n:
                safe_logger.info("cleanup_run_completed | cleaned=%s", n)
            m = sweep_orphaned_storage_prefixes(db, storage)
            if m:
                safe_logger.info("orphan_sweep_completed | cleaned=%s", m)

            """we use default STALE_HOURS value of 30 min for label studio sweep
               using another .env variable seems exaggerated for a value nobody would realistically tune
            """
            k = sweep_orphaned_label_studio_projects(db, label_studio, LABEL_STUDIO_USER_TOKEN)
            if k:
                safe_logger.info("label_studio_orphan_sweep_completed | cleaned=%s", k)
            o = sweep_unarchived_ollama_models(db, ollama_client, ARCHIVE_PREFIX)
            if o:
                safe_logger.info("ollama_orphan_sweep_completed | cleaned=%s", o)
        except Exception as e:
            db.rollback()
            safe_logger.error("cleanup_run_failed", extra={"error_message": str(e)})
            if dev_logger:
                import traceback as _traceback

                dev_logger.error(
                    "cleanup_run_failed_dev",
                    extra={"traceback": _traceback.format_exc()},
                )
        finally:
            db.close()
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
