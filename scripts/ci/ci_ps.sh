#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"
log "ci ps"
# shellcheck disable=SC2086
compose ${COMPOSE_TEST_FILES} ps
