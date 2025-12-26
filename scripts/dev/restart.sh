#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"
log "dev restart"
# shellcheck disable=SC2086
compose ${COMPOSE_FILES} restart
