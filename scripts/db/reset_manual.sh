#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${1:?db name required}"
DB_USER="${DB_USER:-odoo}"

echo "[db] RESET will DROP and RECREATE: ${DB_NAME}"
printf "Type DB name to confirm: "
read -r CONFIRM
[[ "${CONFIRM}" == "${DB_NAME}" ]] || { echo "abort"; exit 1; }

docker compose exec -T db psql -U "${DB_USER}" -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();"
docker compose exec -T db dropdb -U "${DB_USER}" "${DB_NAME}" || true
docker compose exec -T db createdb -U "${DB_USER}" "${DB_NAME}"
echo "[db] reset done: ${DB_NAME}"
