#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$(dirname "$0")/../_lib/common.sh"

guard_prod_forbid
log "ci clean: down -v"
# shellcheck disable=SC2086
compose ${COMPOSE_TEST_FILES} down -v --remove-orphans
