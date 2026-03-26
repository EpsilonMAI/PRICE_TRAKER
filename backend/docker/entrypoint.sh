#!/bin/sh
set -eu  # запускаем shell-скрипт и падаем при ошибках

if [ -n "${DB_HOST:-}" ]; then  # если указан хост БД, ждём пока порт откроется
  echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT:-5432}..."
  while ! nc -z "${DB_HOST}" "${DB_PORT:-5432}"; do  # проверка доступности Postgres
    sleep 1
  done
fi

cd /app/price_tracker

python manage.py migrate --noinput  #применяем миграции автоматически

# если включён DJANGO_COLLECTSTATIC=1, делает collectstatic
if [ "${DJANGO_COLLECTSTATIC:-0}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

# если задан DJANGO_COMMAND:
# выполняем его
if [ -n "${DJANGO_COMMAND:-}" ]; then
  exec sh -c "${DJANGO_COMMAND}"
fi
# иначе:
# запускаем runserver на 0.0.0.0:8000
exec python manage.py runserver 0.0.0.0:${DJANGO_PORT:-8000}
