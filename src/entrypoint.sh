#!/bin/bash
set -euo pipefail

DB_HOST="${DATABASE_SETTINGS__HOST:-taxi-postgres}"
DB_PORT="${DATABASE_SETTINGS__PORT:-5432}"

echo "Ожидание PostgreSQL на ${DB_HOST}:${DB_PORT}..."
until nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done

exec python -m bin
