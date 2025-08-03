# Base image includes Python + Playwright (Ubuntu Jammy)
FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy ║

# Application working directory inside the container
WORKDIR /app

# Install Python dependencies (copied first to leverage build cache)
COPY docker/ml_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the ML backend application code
COPY ml_backend/ /app/

# Expose the Flask/WSGI service port
EXPOSE 6789

# Start the Flask app (unbuffered output for real-time logs)
CMD ["python", "-u", "app.py"]