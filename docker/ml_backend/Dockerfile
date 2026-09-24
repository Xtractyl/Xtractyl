FROM mcr.microsoft.com/playwright/python@sha256:47a65aee64780daa8bad02b37e0ef14902851a3aa7ad0153234f784eb12422b0

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