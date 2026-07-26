# orchestrator/app.py
import os

from api.error_handler import register_error_handlers
from api.routes import register_routes
from flask import Flask
from flask_cors import CORS
from flask_pydantic_spec import FlaskPydanticSpec
from infrastructure.label_studio.label_studio_client import LabelStudioClient
from infrastructure.ollama.ollama_client import OllamaClient
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
        max_retries=int(os.getenv("REDIS_PUSH_MAX_RETRIES", "3")),
        retry_delay_seconds=float(os.getenv("REDIS_PUSH_RETRY_DELAY_SECONDS", "0.5")),
    )
    engine = create_engine(os.getenv("DATABASE_URL"))
    session_factory = sessionmaker(bind=engine)
    label_studio = LabelStudioClient()
    ollama_client = OllamaClient(base_url=os.getenv("OLLAMA_BASE", "http://ollama:11434"))
    app = Flask(__name__)
    # CORS: keep browser frontend working (incl. Authorization header)
    CORS(app, origins=[FRONTEND_ORIGIN], allow_headers=["Content-Type", "Authorization"])

    spec = FlaskPydanticSpec("flask", title="Orchestrator API", version="v1", path="apidoc")
    register_routes(
        app,
        spec,
        storage=storage,
        queue=queue,
        session_factory=session_factory,
        label_studio=label_studio,
        ollama_client=ollama_client,
    )

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
