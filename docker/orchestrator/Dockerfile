FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps
COPY docker/orchestrator/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY orchestrator/ /app/

EXPOSE 5001
CMD ["python", "app.py"]