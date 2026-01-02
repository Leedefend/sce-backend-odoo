#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
export ROOT_DIR

# 新一代统一入口
source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/compose.sh"

log() { printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"; }

: "${DB_NAME:?DB_NAME required}"
: "${DB_USER:?DB_USER required}"

DB_PASSWORD=${DB_PASSWORD:-${DB_USER}}
export DB_USER DB_PASSWORD

# ------------------------------
# 1) reset db（走你刚修好的逻辑）
# ------------------------------
bash "$ROOT_DIR/scripts/db/reset.sh"

# ------------------------------
# 2) install seed + demo modules
# ------------------------------
log "install seed/demo modules on ${DB_NAME}"

compose_dev run --rm -T \
  -e SC_SEED_ENABLED=1 \
  -e SC_BOOTSTRAP_MODE=demo \
  --entrypoint /usr/bin/odoo odoo \
  --config=/etc/odoo/odoo.conf \
  -d "${DB_NAME}" \
  -i smart_construction_seed,smart_construction_demo \
  --without-demo=all \
  --no-http --workers=0 --max-cron-threads=0 \
  --stop-after-init

log "demo reset done: ${DB_NAME}"
