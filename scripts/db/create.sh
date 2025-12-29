#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${1:?db name required}"
DB_USER="${DB_USER:-odoo}"

if command -v docker >/dev/null 2>&1; then
  if docker compose ps db >/dev/null 2>&1; then
    if docker compose exec -T db psql -U "${DB_USER}" -d postgres -At -c "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
      echo "[db] exists: ${DB_NAME}"
      exit 0
    fi
    docker compose exec -T db createdb -U "${DB_USER}" "${DB_NAME}"
    echo "[db] created: ${DB_NAME}"
    exit 0
  fi
fi

echo "[db] docker compose db service not found或无权限"
exit 2
