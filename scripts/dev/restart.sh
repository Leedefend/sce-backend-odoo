#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"
log "dev restart (safe)"

# 1) Recreate nginx and remove orphans to avoid port binding conflicts
# shellcheck disable=SC2086
log "recreate nginx (remove orphans)"
compose ${COMPOSE_FILES} up -d --force-recreate --remove-orphans nginx

# 2) Fast restart deps (avoid stale bind-mount issues on odoo)
compose ${COMPOSE_FILES} restart db redis || true

# 3) Recreate odoo to avoid stale bind-mounts in WSL/Docker Desktop
log "recreate odoo (avoid stale bind-mount)"
compose ${COMPOSE_FILES} up -d --force-recreate ${ODOO_SERVICE:-odoo}

# 4) Show status
compose ${COMPOSE_FILES} ps
