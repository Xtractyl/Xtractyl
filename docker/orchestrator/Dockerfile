FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps
COPY docker/orchestrator/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Code is bind-mounted at runtime by docker compose:
#   - ${ORCH_APP_DIR:-./orchestrator}:/app
# so we don't COPY the source here.

EXPOSE 5001
CMD ["python", "app.py"]