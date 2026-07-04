FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV WORKOPS_DATA=/app/data

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates openssh-client rclone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backup_manager ./backup_manager
COPY static ./static
COPY run.py ./run.py

RUN mkdir -p /app/data

EXPOSE 8099

CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8099"]
