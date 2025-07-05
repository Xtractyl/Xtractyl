FROM python:3.10-slim

WORKDIR /app

COPY orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY orchestrator/ /app/

CMD ["tail", "-f", "/dev/null"]