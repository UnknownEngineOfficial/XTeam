#!/bin/bash
# Backend startup script with migrations

set -e

echo "Waiting for database to be ready..."
sleep 2

echo "Running database migrations..."
# Use advisory lock to prevent concurrent migrations
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
