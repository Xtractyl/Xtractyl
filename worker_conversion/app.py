# worker_conversion/app.py
from __future__ import annotations

from config import MINIO_ACCESS_KEY, MINIO_ENDPOINT, MINIO_SECRET_KEY, REDIS_HOST, REDIS_PORT
from consumer import run
from minio import Minio
from redis import Redis


def main() -> None:
    redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True)
    minio_client = Minio(
        MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False
    )
    run(redis_conn, minio_client)


if __name__ == "__main__":
    main()
