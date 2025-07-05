FROM python:3.10-slim

# Prevents Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Ensures stdout/stderr are unbuffered
ENV PYTHONUNBUFFERED=1

# Install system dependencies (for OCR etc.)
RUN apt-get update && \
    apt-get install -y tesseract-ocr libgl1 && \
    rm -rf /var/lib/apt/lists/*

# Install docling
RUN pip install --no-cache-dir docling

WORKDIR /app

ENTRYPOINT ["tail", "-f", "/dev/null"]