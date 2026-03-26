FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential libpq-dev netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY price_tracker ./price_tracker
COPY docker ./docker

RUN chmod +x /app/docker/entrypoint.sh

WORKDIR /app/price_tracker

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
