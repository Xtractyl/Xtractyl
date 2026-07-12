FROM python:3.10.19-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY docker/cleanup/requirements.lock.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY orchestrator/cleanup_loop.py /app/cleanup_loop.py
COPY orchestrator/domain/cleanup.py /app/domain/cleanup.py
COPY orchestrator/domain/errors.py /app/domain/errors.py
COPY orchestrator/infrastructure/interfaces/storage.py /app/infrastructure/interfaces/storage.py
COPY orchestrator/infrastructure/storage/minio_storage.py /app/infrastructure/storage/minio_storage.py
COPY shared/logging_utils.py /app/utils/logging_utils.py

CMD ["python", "cleanup_loop.py"]