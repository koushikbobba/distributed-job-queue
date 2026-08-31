#!/bin/sh
set -e

echo "==> Waiting for PostgreSQL ($POSTGRES_HOST:$POSTGRES_PORT)..."
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 0.5
done

echo "==> Waiting for Redis (redis:6379)..."
while ! nc -z redis 6379; do
  sleep 0.5
done

echo "==> Starting Celery Worker (Queues: high_priority, default_priority, low_priority)..."
exec celery -A config worker \
    --loglevel=INFO \
    --concurrency=4 \
    -Q high_priority,default_priority,low_priority \
    -n worker@%h
