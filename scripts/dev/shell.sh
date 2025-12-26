#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"
log "enter odoo container shell"
# shellcheck disable=SC2086
compose ${COMPOSE_FILES} exec odoo bash
