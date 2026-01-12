#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
export ROOT_DIR

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/compose.sh"

log() { printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"; }

: "${DB_NAME:?DB_NAME required}"
: "${DB_USER:?DB_USER required}"

DB_PASSWORD=${DB_PASSWORD:-${DB_USER}}
export DB_USER DB_PASSWORD

# 1) reset db
log "demo reset start: ${DB_NAME}"
log "db reset start: ${DB_NAME}"
bash "$ROOT_DIR/scripts/db/reset.sh"
log "db reset done: ${DB_NAME}"

# 2) install seed + demo modules
SC_WITH_DEMO="${SC_WITH_DEMO:-1}"
if [[ "${SC_WITH_DEMO}" == "1" ]]; then
  WITHOUT_DEMO_FLAG="--without-demo=0"
else
  WITHOUT_DEMO_FLAG="--without-demo=all"
fi

DEMO_LOGFILE="${DEMO_LOGFILE:-/tmp/demo_install.log}"
ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH:-/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux}"

log "install seed/demo modules on ${DB_NAME}"

compose_dev run --rm -T \
  -e SC_SEED_ENABLED=1 \
  -e SC_BOOTSTRAP_MODE=demo \
  -e DB_NAME="${DB_NAME}" \
  -e DB_USER="${DB_USER}" \
  -e DB_PASSWORD="${DB_PASSWORD}" \
  -e ODOO_CONF="${ODOO_CONF}" \
  -e ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH}" \
  -e WITHOUT_DEMO_FLAG="${WITHOUT_DEMO_FLAG}" \
  -e DEMO_LOGFILE="${DEMO_LOGFILE}" \
  --entrypoint /bin/bash odoo -lc 'bash -s' <<'BASH_IN_CONTAINER'
set -euo pipefail
set -o pipefail

odoo --config="$ODOO_CONF" \
  --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  --addons-path="$ODOO_ADDONS_PATH" \
  -d "$DB_NAME" \
  -i smart_construction_core,smart_construction_seed,smart_construction_demo \
  $WITHOUT_DEMO_FLAG \
  --no-http --workers=0 --max-cron-threads=0 --stop-after-init \
  2>&1 | tee "$DEMO_LOGFILE"

rc=${PIPESTATUS[0]}
if [ "$rc" -ne 0 ]; then
  tail -n 200 "$DEMO_LOGFILE" || true
fi
exit "$rc"
BASH_IN_CONTAINER

log "demo rebuild done: ${DB_NAME}"
