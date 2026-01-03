#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
export ROOT_DIR

DB_NAME="${1:?db name required}"
export DB_NAME

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

echo "[db] RESET will DROP and RECREATE: ${DB_NAME}"
printf "Type DB name to confirm: "
read -r CONFIRM
[[ "${CONFIRM}" == "${DB_NAME}" ]] || { echo "abort"; exit 1; }

compose_dev exec -T db psql -U "${DB_USER}" -d postgres -v ON_ERROR_STOP=1 -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();"
compose_dev exec -T db dropdb -U "${DB_USER}" "${DB_NAME}" || true
compose_dev exec -T db createdb -U "${DB_USER}" "${DB_NAME}"
echo "[db] reset done: ${DB_NAME}"
