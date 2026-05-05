#!/bin/sh
set -eu

INTERVAL_SECONDS="${PRICE_UPDATE_INTERVAL_SECONDS:-3600}"

case "$INTERVAL_SECONDS" in
  ''|*[!0-9]*)
    echo "PRICE_UPDATE_INTERVAL_SECONDS must be a positive integer"
    exit 1
    ;;
esac

if [ "$INTERVAL_SECONDS" -le 0 ]; then
  echo "PRICE_UPDATE_INTERVAL_SECONDS must be greater than 0"
  exit 1
fi

cd /app/price_tracker

echo "Starting price history scheduler with ${INTERVAL_SECONDS}s interval"

WEEKLY_DIGEST_INTERVAL=604800  # 7 дней в секундах
elapsed_since_digest=0

while true; do
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Running update_price_history"
  python manage.py update_price_history

  elapsed_since_digest=$((elapsed_since_digest + INTERVAL_SECONDS))
  if [ "$elapsed_since_digest" -ge "$WEEKLY_DIGEST_INTERVAL" ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Running send_weekly_digest"
    python manage.py send_weekly_digest
    elapsed_since_digest=0
  fi

  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Sleeping for ${INTERVAL_SECONDS}s"
  sleep "$INTERVAL_SECONDS"
done
