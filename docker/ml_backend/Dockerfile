FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

WORKDIR /app

# Requirements installieren
COPY docker/ml_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY ml_backend/ /app/

EXPOSE 6789

# Direkt Flask-App starten
CMD ["python", "-u", "app.py"]