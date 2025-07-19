FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies (Tesseract etc.)
RUN apt-get update && \
    apt-get install -y tesseract-ocr libgl1 && \
    rm -rf /var/lib/apt/lists/*

# Install Flask + Docling
RUN pip install --no-cache-dir flask docling

WORKDIR /app
COPY docling/app.py .
COPY docker/docling/requirements.txt .

# Flask runs via docker-compose command