#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

: "${DB_NAME:?DB_NAME required}"

log "[verify.p0.flow] reset db=${DB_NAME}"
DB_NAME="${DB_NAME}" bash scripts/db/reset.sh

log "[verify.p0.flow] install core"
DB_NAME="${DB_NAME}" MODULE="smart_construction_core" bash scripts/mod/install.sh

log "[verify.p0.flow] install seed"
DB_NAME="${DB_NAME}" MODULE="smart_construction_seed" bash scripts/mod/install.sh

log "[verify.p0.flow] run p0 verification"
DB_NAME="${DB_NAME}" bash scripts/verify/p0_base.sh

log "[verify.p0.flow] done db=${DB_NAME}"
