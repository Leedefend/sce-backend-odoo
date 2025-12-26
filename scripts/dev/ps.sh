#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"
# shellcheck disable=SC2086
compose ${COMPOSE_FILES} ps
