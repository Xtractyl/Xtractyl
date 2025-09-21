# docker/docling/Dockerfile
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies (Tesseract + OpenGL lib for headless rendering)
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
WORKDIR /app
COPY docker/docling/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the application code (including utils/)
COPY docling/ /app/

# Document the port
EXPOSE 5004

# Start Flask
CMD ["sh", "-c", "flask --app app.py run --host=0.0.0.0 --port=${DOCLING_PORT:-5004}"]