FROM mcr.microsoft.com/playwright/python@sha256:6679b332bf4d772a9bf2bb3d7715f8e35bff5808c9d06e2599c767f828f8e3f1

WORKDIR /app

# install requirements
COPY docker/ml_backend/requirements.lock.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt 

# copy app code
COPY ml_backend/ /app/

# add centralized logger code
COPY shared/logging_utils.py /app/utils/logging_utils.py  

EXPOSE 6789

# start flask
CMD ["python", "-u", "app.py"]