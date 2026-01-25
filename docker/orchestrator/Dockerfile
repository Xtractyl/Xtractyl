FROM python:3.10.19-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps
COPY docker/orchestrator/requirements.lock.txt /app/requirements.txt
COPY docker/orchestrator/requirements-dev.txt /app/requirements-dev.txt

RUN pip install --no-cache-dir -r /app/requirements.txt -r /app/requirements-dev.txt

COPY orchestrator/ /app/

EXPOSE 5001
CMD ["python", "app.py"]