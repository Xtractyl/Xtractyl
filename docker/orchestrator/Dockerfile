FROM python:3.10.19-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps
COPY docker/orchestrator/requirements.lock.txt /app/requirements.txt
COPY docker/orchestrator/requirements-dev.txt /app/requirements-dev.txt

RUN pip install --no-cache-dir -r /app/requirements.txt -r /app/requirements-dev.txt

# add worker code
COPY orchestrator/ /app/

# add centralized logger code
COPY shared/logging_utils.py /app/utils/logging_utils.py  


EXPOSE 5001
CMD ["sh", "-c", "alembic upgrade head && python app.py"]