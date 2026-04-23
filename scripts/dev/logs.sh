#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"
log "dev logs"
# shellcheck disable=SC2086
compose ${COMPOSE_FILES} logs -f --tail=200 odoo
