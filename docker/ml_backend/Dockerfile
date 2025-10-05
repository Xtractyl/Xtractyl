FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

WORKDIR /app

# install requirements
COPY docker/ml_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app code
COPY ml_backend/ /app/

EXPOSE 6789

# start flask
CMD ["python", "-u", "app.py"]