#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"
log "ci logs (tail)"
# shellcheck disable=SC2086
compose ${COMPOSE_TEST_FILES} logs --tail="${CI_TAIL_ODOO}" odoo || true
compose ${COMPOSE_TEST_FILES} logs --tail="${CI_TAIL_DB}" db || true
compose ${COMPOSE_TEST_FILES} logs --tail="${CI_TAIL_REDIS}" redis || true
