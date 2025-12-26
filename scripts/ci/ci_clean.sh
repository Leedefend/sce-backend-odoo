#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"
log "ci clean: down -v"
# shellcheck disable=SC2086
compose ${COMPOSE_TEST_FILES} down -v --remove-orphans
