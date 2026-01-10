FROM mcr.microsoft.com/playwright/python@sha256:0ff30156b1035e3bc24d92f67fb57e86bd1fef126b544f32c699ce1ae9b3b692

WORKDIR /app

# install requirements
COPY docker/ml_backend/requirements.lock.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy app code
COPY ml_backend/ /app/

EXPOSE 6789

# start flask
CMD ["python", "-u", "app.py"]