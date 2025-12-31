#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

log() { printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"; }

: "${DB_NAME:?DB_NAME required}"
: "${DB_USER:?DB_USER required}"

DB_PASSWORD=${DB_PASSWORD:-${DB_USER}}
export DB_USER DB_PASSWORD

log "db reset: ${DB_NAME}"
compose_dev up -d db redis

DB_READY_TIMEOUT="${DB_READY_TIMEOUT:-120}"
DB_READY_INTERVAL="${DB_READY_INTERVAL:-1}"
log "db wait: pg_isready (timeout ${DB_READY_TIMEOUT}s)"
pg_isready_check() {
  if command -v timeout >/dev/null 2>&1; then
    timeout 2s bash -lc "ROOT_DIR='${ROOT_DIR}' COMPOSE_BIN='${COMPOSE_BIN}' PROJECT='${PROJECT}' \
      source '${ROOT_DIR}/scripts/common/env.sh'; \
      source '${ROOT_DIR}/scripts/common/compose.sh'; \
      compose_dev exec -T db pg_isready -U '${DB_USER}' -d postgres -t 2" >/dev/null 2>&1
  else
    compose_dev exec -T db pg_isready -U "${DB_USER}" -d postgres -t 2 >/dev/null 2>&1
  fi
}

for i in $(seq 1 "$DB_READY_TIMEOUT"); do
  if pg_isready_check; then
    log "db ready"
    break
  fi
  if [[ "$i" -eq "$DB_READY_TIMEOUT" ]]; then
    log "db NOT ready after ${DB_READY_TIMEOUT}s"
    compose_dev exec -T db pg_isready -U "${DB_USER}" -d postgres -t 2 || true
    compose_dev logs --tail=200 db || true
    exit 2
  fi
  if (( i % 10 == 0 )); then
    log "db wait: pg_isready (${i}/${DB_READY_TIMEOUT})"
  fi
  sleep "$DB_READY_INTERVAL"
done

# terminate existing connections to allow drop
compose_dev exec -T db psql -U "${DB_USER}" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}';" >/dev/null || true

compose_dev exec -T db psql -U "${DB_USER}" -d postgres -c \
  "DROP DATABASE IF EXISTS ${DB_NAME};"
compose_dev exec -T db psql -U "${DB_USER}" -d postgres -c \
  "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER} TEMPLATE template0 ENCODING 'UTF8';"

# 统一 Odoo DB 参数（后续所有操作必须带，避免掉回本机 socket）
ODOO_DB_ARGS=(
  --db_host=db --db_port=5432
  --db_user="${DB_USER}" --db_password="${DB_PASSWORD}"
)

log "odoo init base (stop-after-init): ${DB_NAME}"
compose_dev run --rm -T \
  --entrypoint /usr/bin/odoo odoo \
  --config=/etc/odoo/odoo.conf \
  -d "${DB_NAME}" \
  "${ODOO_DB_ARGS[@]}" \
  -i base \
  --without-demo=all \
  --no-http --workers=0 --max-cron-threads=0 \
  --stop-after-init

log "install bootstrap module: smart_construction_bootstrap"
compose_dev run --rm -T \
  --entrypoint /usr/bin/odoo odoo \
  --config=/etc/odoo/odoo.conf \
  -d "${DB_NAME}" \
  "${ODOO_DB_ARGS[@]}" \
  -i smart_construction_bootstrap \
  --without-demo=all \
  --no-http --workers=0 --max-cron-threads=0 \
  --stop-after-init

log "db reset done: ${DB_NAME}"
