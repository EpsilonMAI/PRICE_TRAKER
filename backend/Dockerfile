FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Системные зависимости + Google Chrome ──────────────────────────
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
       build-essential libpq-dev netcat-openbsd \
       # Зависимости для headless Chrome (шрифты, графика, dbus)
       wget gnupg2 curl unzip \
       fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
       libatk1.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
       libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
       libxrandr2 xdg-utils libxss1 libxtst6 \
    # Устанавливаем Google Chrome Stable
    && wget -qO /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install --yes --no-install-recommends /tmp/chrome.deb \
    && rm /tmp/chrome.deb \
    && rm -rf /var/lib/apt/lists/*

# ── Python-зависимости ─────────────────────────────────────────────
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ── Код приложения ─────────────────────────────────────────────────
COPY price_tracker ./price_tracker
COPY docker ./docker

RUN chmod +x /app/docker/entrypoint.sh

WORKDIR /app/price_tracker

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
