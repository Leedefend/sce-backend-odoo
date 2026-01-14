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
ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH:-/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux}"

STOP_ODOO=0
restore_odoo() {
  if [[ "${STOP_ODOO}" == "1" ]]; then
    log "start odoo service after db reset"
    compose_dev up -d odoo || true
  fi
}
trap 'status=$?; restore_odoo; exit $status' EXIT

case "${DB_NAME}" in
  "" )
    log "DB_NAME is empty; refuse to proceed"
    exit 2
    ;;
  postgres|template0|template1)
    log "refuse to drop system database: ${DB_NAME}"
    exit 2
    ;;
esac

log "db reset: ${DB_NAME}"

if ! compose_dev ps -q db | grep -q .; then
  log "db container not running; run 'make up' first"
  exit 2
fi

if [[ "${DB_RESET_STOP_ODOO:-1}" == "1" && "${DB_NAME}" == "sc_demo" ]]; then
  if compose_dev ps -q odoo | grep -q .; then
    log "stop odoo service to release sc_demo connections"
    compose_dev stop odoo
    STOP_ODOO=1
  fi
fi

DB_READY_TIMEOUT="${DB_READY_TIMEOUT:-120}"
DB_READY_INTERVAL="${DB_READY_INTERVAL:-1}"
DB_READY_USER="${DB_READY_USER:-${DB_USER}}"
DB_READY_DB="${DB_READY_DB:-postgres}"
log "db wait: healthcheck/pg_isready (timeout ${DB_READY_TIMEOUT}s)"

DB_CID="$(compose_dev ps -q db | head -n 1)"
if [[ -z "${DB_CID}" ]]; then
  log "db container not found (compose project mismatch?)"
  exit 2
fi
if [[ -n "${PROJECT:-}" ]]; then
  db_project="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "${DB_CID}" 2>/dev/null || true)"
  if [[ -n "${db_project}" && "${db_project}" != "${PROJECT}" ]]; then
    log "db container project mismatch: got=${db_project} expected=${PROJECT}"
    exit 2
  fi
fi

for i in $(seq 1 "$DB_READY_TIMEOUT"); do
  health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${DB_CID}" 2>/dev/null || echo "unknown")"
  if [[ "${health}" == "healthy" ]]; then
    log "db ready (healthcheck=healthy)"
    break
  fi
  if [[ "${health}" == "none" || "${health}" == "unknown" ]]; then
    if docker exec -i "${DB_CID}" \
      pg_isready -U "${DB_READY_USER}" -d "${DB_READY_DB}" -t 2 >/dev/null 2>&1; then
      log "db ready (pg_isready)"
      break
    fi
  fi
  if [[ "$i" -eq 1 ]]; then
    docker exec -i "${DB_CID}" \
      pg_isready -U "${DB_READY_USER}" -d "${DB_READY_DB}" -t 2 || true
  fi
  if [[ "$i" -eq "$DB_READY_TIMEOUT" ]]; then
    log "db NOT ready after ${DB_READY_TIMEOUT}s (health=${health})"
    docker logs --tail=200 "${DB_CID}" || true
    exit 2
  fi
  if (( i % 10 == 0 )); then
    log "db wait: healthcheck/pg_isready (${i}/${DB_READY_TIMEOUT})"
  fi
  sleep "$DB_READY_INTERVAL"
done

# terminate existing connections to allow drop
log "db terminate connections: ${DB_NAME}"
docker exec -T -e PGPASSWORD="${DB_PASSWORD}" "${DB_CID}" psql -U "${DB_USER}" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}';" >/dev/null || true

log "db drop: ${DB_NAME}"
docker exec -T -e PGPASSWORD="${DB_PASSWORD}" "${DB_CID}" psql -U "${DB_USER}" -d postgres -c \
  "DROP DATABASE IF EXISTS ${DB_NAME};"
log "db create: ${DB_NAME}"
docker exec -T -e PGPASSWORD="${DB_PASSWORD}" "${DB_CID}" psql -U "${DB_USER}" -d postgres -c \
  "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER} TEMPLATE template0 ENCODING 'UTF8';"

# 统一 Odoo DB 参数（后续所有操作必须带，避免掉回本机 socket）
ODOO_DB_ARGS=(
  --db_host=db --db_port=5432
  --db_user="${DB_USER}" --db_password="${DB_PASSWORD}"
  --addons-path="${ODOO_ADDONS_PATH}"
)

log "odoo init base (stop-after-init): ${DB_NAME}"
compose_dev run --rm -T \
  --entrypoint /usr/bin/odoo odoo \
  --config="$ODOO_CONF" \
  -d "${DB_NAME}" \
  "${ODOO_DB_ARGS[@]}" \
  -i base \
  --without-demo=all \
  --no-http --workers=0 --max-cron-threads=0 \
  --stop-after-init

log "install bootstrap module: smart_construction_bootstrap"
compose_dev run --rm -T \
  --entrypoint /usr/bin/odoo odoo \
  --config="$ODOO_CONF" \
  -d "${DB_NAME}" \
  "${ODOO_DB_ARGS[@]}" \
  -i smart_construction_bootstrap \
  --without-demo=all \
  --no-http --workers=0 --max-cron-threads=0 \
  --stop-after-init

log "db reset done: ${DB_NAME}"
