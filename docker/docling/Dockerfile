# =========================
# Stage 1: load models
# =========================
FROM python:3.10.19-slim AS docling_models

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies (Tesseract + OpenGL lib for headless rendering)
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Docling & Co from requirements
COPY docker/docling/requirements.lock.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# pull all models (reduce to the models you need if preferred)
RUN docling-tools models download --all -o /opt/docling-models



# =========================
# Stage 2: Runtime / App
# =========================
FROM python:3.10.19-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python-Dependencies for app
COPY docker/docling/requirements.lock.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy models from stage 1
COPY --from=docling_models /opt/docling-models /opt/docling-models
ENV DOCLING_ARTIFACTS_PATH=/opt/docling-models

# App-Code
COPY docling/ /app/

EXPOSE 5004

CMD ["sh", "-c", "flask --app app.py run --host=0.0.0.0 --port=${DOCLING_PORT:-5004}"]