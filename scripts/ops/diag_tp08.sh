#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$ROOT_DIR/scripts/_lib/common.sh"

guard_prod_forbid

log "diag.tp08: docker access"
if docker info >/dev/null 2>&1; then
  echo "OK docker access"
else
  echo "FAIL docker access"
fi

log "diag.tp08: compose project"
echo "PROJECT=${PROJECT:-${COMPOSE_PROJECT_NAME:-sc-backend-odoo}}"

log "diag.tp08: services"
compose ps || true

log "diag.tp08: odoo logs (last 200)"
compose logs --tail 200 odoo || true

log "diag.tp08: db/redis health"
compose ps db redis || true
