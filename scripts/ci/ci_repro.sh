#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"
log "ci repro: keep artifacts, show last log path"
echo "${CI_ARTIFACT_DIR}/${CI_LOG}"
