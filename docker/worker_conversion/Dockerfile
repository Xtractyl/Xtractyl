FROM python:3.11.14-slim

WORKDIR /app

COPY docker/worker_conversion/requirements.lock.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY worker_conversion /app/

CMD ["python", "app.py"]