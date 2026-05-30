FROM python:3.11.14-slim

WORKDIR /app

# Install deps
COPY docker/worker/requirements.lock.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy worker code
COPY worker /app/

# add centralized logger code
COPY shared/logging_utils.py /app/utils/logging_utils.py  

# Default command
CMD ["python", "app.py"]