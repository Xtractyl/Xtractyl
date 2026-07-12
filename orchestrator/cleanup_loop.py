# orchestrator/cleanup_loop.py
import os
import time

from domain.cleanup import cleanup_stale_conversion_jobs
from infrastructure.storage.minio_storage import MinioStorage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.logging_utils import safe_logger

INTERVAL = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "3600"))
STALE_HOURS = int(os.getenv("CLEANUP_STALE_AFTER_HOURS", "2"))

DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_XTRACTYL_USER', 'xtractyl')}:"
    f"{os.getenv('POSTGRES_XTRACTYL_PASSWORD', 'yourpassword')}@"
    f"{os.getenv('POSTGRES_XTRACTYL_CONTAINER_NAME', 'postgres_xtractyl')}:5432/"
    f"{os.getenv('POSTGRES_XTRACTYL_DB', 'xtractyl')}"
)
engine = create_engine(DATABASE_URL)
session_factory = sessionmaker(bind=engine)

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
        except Exception:
            db.rollback()
            safe_logger.error("cleanup_run_failed")
        finally:
            db.close()
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
