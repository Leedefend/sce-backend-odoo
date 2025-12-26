#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

log "upgrade gate via run_ci"
bash "$(dirname "$0")/run_ci.sh"
