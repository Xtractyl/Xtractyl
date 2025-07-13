FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY docker/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 5001

# Start the Flask app
CMD ["python", "app.py"]