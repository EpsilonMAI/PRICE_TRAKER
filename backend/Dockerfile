FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Системные зависимости + Chromium ───────────────────────────────
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
       build-essential libpq-dev netcat-openbsd \
       wget gnupg2 curl unzip \
       fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
       libatk1.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
       libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
       libxrandr2 xdg-utils libxss1 libxtst6 \
       chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# ── Python-зависимости ─────────────────────────────────────────────
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ── Код приложения ─────────────────────────────────────────────────
COPY price_tracker ./price_tracker
COPY docker ./docker

RUN chmod +x /app/docker/entrypoint.sh /app/docker/scheduler.sh

WORKDIR /app/price_tracker

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
