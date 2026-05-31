FROM python:3.11.14-slim

WORKDIR /app

COPY docker/worker_conversion/requirements.lock.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# add worker_conversion code
COPY worker_conversion /app/

# add centralied logger code
COPY shared/logging_utils.py /app/utils/logging_utils.py  

CMD ["python", "app.py"]