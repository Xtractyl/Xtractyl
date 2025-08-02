# docker/docling/Dockerfile
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps (Tesseract + OpenGL lib für headless Rendering)
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Abhängigkeiten zuerst (bessere Layer-Caches)
WORKDIR /app
COPY docker/docling/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt


# App-Code KOMPLETT kopieren (inkl. utils/)
COPY docling/ /app/

# Optional: Port dokumentieren
EXPOSE 5004

# Flask starten
CMD ["flask", "--app", "app.py", "run", "--host=0.0.0.0", "--port=5004"]