FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY docker/worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy worker code
COPY worker /app/worker

# Default command
CMD ["python", "-m", "worker.prelabel_worker"]