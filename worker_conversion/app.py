# worker_conversion/app.py
from __future__ import annotations

from config import (
    DOCLING_URL,
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    ORCHESTRATOR_CALLBACK_URL,
    REDIS_HOST,
    REDIS_PORT,
    WORKER_DOCLING_TIMEOUT_SECONDS,
)
from consumer import run
from infrastructure.callback.orchestrator_callback_client import OrchestratorCallbackClient
from infrastructure.docling.docling_client import DoclingHttpClient
from infrastructure.storage.minio_storage import MinioConversionStorage
from minio import Minio
from redis import Redis


def main() -> None:
    redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True)
    minio_client = Minio(
        MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False
    )

    storage = MinioConversionStorage(minio_client)
    docling = DoclingHttpClient(DOCLING_URL, WORKER_DOCLING_TIMEOUT_SECONDS)
    callback = OrchestratorCallbackClient(ORCHESTRATOR_CALLBACK_URL)

    run(redis_conn, storage, docling, callback)


if __name__ == "__main__":
    main()
