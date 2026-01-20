#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

DB_NAME="${DB_NAME:-${DB:-sc_p3}}"

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"
# shellcheck source=../_lib/common.sh
source "$ROOT_DIR/scripts/_lib/common.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME is required}"
if [[ "$DB_NAME" != "sc_p3" ]]; then
  echo "FAIL p3.smoke only supports DB=sc_p3 (got DB=${DB_NAME})"
  echo "Fix: make p3.smoke DB=sc_p3"
  exit 1
fi

ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH:-/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux}"
DB_PASSWORD="${DB_PASSWORD:-${DB_USER}}"

status=0

log "p3.validate: docker access"
if docker info >/dev/null 2>&1; then
  echo "OK docker access"
else
  echo "FAIL docker access"
  status=1
fi

log "p3.validate: compose services"
if ! compose_dev ps >/dev/null 2>&1; then
  echo "FAIL compose ps"
  status=1
fi

log "p3.validate: odoo/db status"
ps_out="$(compose_dev ps odoo db || true)"
echo "$ps_out"
if ! echo "$ps_out" | grep -E -q "odoo"; then
  echo "FAIL odoo service not found"
  status=1
fi
if ! echo "$ps_out" | grep -E -q "db"; then
  echo "FAIL db service not found"
  status=1
fi
if ! echo "$ps_out" | grep -E -q "(Up|running)"; then
  echo "FAIL services not running"
  status=1
fi

if [[ "$status" -ne 0 ]]; then
  echo "RESULT: FAIL"
  exit 1
fi

log "p3.validate: db existence"
db_exists="$(compose_dev exec -T -e PGPASSWORD="$DB_PASSWORD" db psql -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}';" || true)"
db_exists="$(echo "$db_exists" | tr -d '[:space:]')"
if [[ "$db_exists" != "1" ]]; then
  echo "FAIL database ${DB_NAME} not found"
  echo "Fix: make db.reset DB=${DB_NAME}  # or make mod.upgrade MODULE=smart_construction_core DB=${DB_NAME}"
  echo "RESULT: FAIL"
  exit 1
fi

log "p3.validate: odoo shell smoke"
compose_dev exec -T \
  -e PYTHONWARNINGS=ignore \
  odoo odoo shell -d "$DB_NAME" \
  --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  --addons-path="$ODOO_ADDONS_PATH" \
  --logfile=/dev/null --log-level=warn \
  < "$ROOT_DIR/scripts/ops/p3_runtime_smoke.py"

if [[ "$?" -eq 0 ]]; then
  echo "RESULT: PASS"
  exit 0
fi

echo "RESULT: FAIL"
exit 1
