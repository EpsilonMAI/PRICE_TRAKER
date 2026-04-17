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

while true; do
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Running update_price_history"
  python manage.py update_price_history
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Sleeping for ${INTERVAL_SECONDS}s"
  sleep "$INTERVAL_SECONDS"
done
