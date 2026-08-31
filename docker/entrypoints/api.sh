#!/bin/sh
set -e

echo "==> Waiting for PostgreSQL ($POSTGRES_HOST:$POSTGRES_PORT)..."
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 0.5
done
echo "==> PostgreSQL is up and ready!"

echo "==> Waiting for Redis (redis:6379)..."
while ! nc -z redis 6379; do
  sleep 0.5
done
echo "==> Redis is up and ready!"

echo "==> Running Database Migrations..."
python manage.py migrate --noinput

echo "==> Collecting Static Files..."
python manage.py collectstatic --noinput --clear || true

echo "==> Starting Django Development Server on 0.0.0.0:8000..."
exec python manage.py runserver 0.0.0.0:8000
