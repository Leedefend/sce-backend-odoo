#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

: "${DB_NAME:?DB_NAME required}"
: "${DB_USER:?DB_USER required}"
: "${COMPOSE_FILES:?COMPOSE_FILES required}"

DB_PASSWORD=${DB_PASSWORD:-${DB_USER}}

# 1) reset db (reuse db.reset logic)
bash "$(dirname "$0")/../db/reset.sh"

# 2) install seed + demo modules
log "install seed/demo modules on ${DB_NAME}"
compose ${COMPOSE_FILES} run --rm -T \
  -e SC_SEED_ENABLED=1 \
  -e SC_BOOTSTRAP_MODE=demo \
  --entrypoint bash odoo -lc "
    exec /usr/bin/odoo \
      --db_host=db --db_port=5432 --db_user=${DB_USER} --db_password=${DB_PASSWORD} \
      -d ${DB_NAME} \
      --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,${ADDONS_EXTERNAL_MOUNT} \
      -i smart_construction_seed,smart_construction_demo \
      --without-demo=all \
      --no-http --workers=0 --max-cron-threads=0 \
      --stop-after-init
  "

log "demo reset done: ${DB_NAME}"
