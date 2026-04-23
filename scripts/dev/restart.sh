#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"
log "dev restart (safe)"

# 1) Ensure deps are up (odoo UI depends on db/redis)
# shellcheck disable=SC2086
log "ensure deps (db/redis)"
compose ${COMPOSE_FILES} up -d db redis

# 2) Recreate odoo to apply UI/config changes
log "recreate odoo (apply UI changes)"
compose ${COMPOSE_FILES} up -d --force-recreate ${ODOO_SERVICE:-odoo}

# 3) Show status
compose ${COMPOSE_FILES} ps
