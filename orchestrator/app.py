# orchestrator/app.py
import os

from api.error_handler import register_error_handlers
from api.routes import register_routes
from flask import Flask
from flask_cors import CORS
from flask_pydantic_spec import FlaskPydanticSpec
from infrastructure.queue.redis_queue import RedisQueue
from infrastructure.storage.minio_storage import MinioStorage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.logging_utils import dev_logger, safe_logger

safe_logger.info("orchestrator_starting")
if dev_logger:
    dev_logger.info("dev_logging_enabled")


FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN", f"http://localhost:{os.getenv('FRONTEND_PORT', '5173')}"
)
APP_PORT = int(os.getenv("ORCH_PORT", "5001"))


def create_app() -> Flask:
    storage = MinioStorage(
        endpoint=os.getenv("MINIO_CONTAINER_NAME", "minio")
        + ":"
        + os.getenv("MINIO_API_PORT", "9000"),
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "yourpassword"),
        bucket=os.getenv("MINIO_BUCKET", "xtractyl"),
        presign_expiry_seconds=int(os.getenv("MINIO_PRESIGN_EXPIRY_SECONDS", "3600")),
    )
    queue = RedisQueue(
        host=os.getenv("REDIS_HOST", "job_queue"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=1,
        queue_name="conversion_jobs",
    )
    engine = create_engine(os.getenv("DATABASE_URL"))
    session_factory = sessionmaker(bind=engine)
    app = Flask(__name__)
    # CORS: keep browser frontend working (incl. Authorization header)
    CORS(app, origins=[FRONTEND_ORIGIN], allow_headers=["Content-Type", "Authorization"])

    spec = FlaskPydanticSpec("flask", title="Orchestrator API", version="v1", path="apidoc")
    register_routes(app, spec, storage=storage, queue=queue, session_factory=session_factory)

    register_error_handlers(
        app=app,
        logger_safe=safe_logger,
        logger_dev=dev_logger,
    )
    spec.register(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)
