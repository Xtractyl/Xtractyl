FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app

# Copy requirements and install dependencies
COPY docker/ml_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ml_backend/ /app/

# Copy and set entrypoint
COPY docker/ml_backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 6789

ENTRYPOINT ["/entrypoint.sh"]