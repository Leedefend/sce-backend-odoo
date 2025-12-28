#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

: "${DB_NAME:?DB_NAME required}"
: "${DB_USER:?DB_USER required}"
: "${COMPOSE_FILES:?COMPOSE_FILES required}"

DB_PASSWORD=${DB_PASSWORD:-${DB_USER}}

# 1) reset db (reuse db.reset logic)
bash "$(dirname "$0")/../db/reset.sh"

# 2) install demo module (brings in smart_construction_core dependency)
log "install demo module on ${DB_NAME}"
compose ${COMPOSE_FILES} run --rm -T \
  --entrypoint bash odoo -lc "
    exec /usr/bin/odoo \
      --db_host=db --db_port=5432 --db_user=${DB_USER} --db_password=${DB_PASSWORD} \
      -d ${DB_NAME} \
      --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,${ADDONS_EXTERNAL_MOUNT} \
      -i smart_construction_demo \
      --without-demo=all \
      --no-http --workers=0 --max-cron-threads=0 \
      --stop-after-init
  "

log "demo reset done: ${DB_NAME}"
