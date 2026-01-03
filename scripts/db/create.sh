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

if compose_dev ps db >/dev/null 2>&1; then
  if compose_dev exec -T db psql -U "${DB_USER}" -d postgres -At \
    -c "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
    echo "[db] exists: ${DB_NAME}"
    exit 0
  fi
  compose_dev exec -T db createdb -U "${DB_USER}" "${DB_NAME}"
  echo "[db] created: ${DB_NAME}"
  exit 0
fi

echo "[db] compose db service not found或无权限"
exit 2
