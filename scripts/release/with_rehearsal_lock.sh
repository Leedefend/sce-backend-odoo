#!/usr/bin/env bash
set -euo pipefail
db_name="${1:?database name required}"
shift
SC_ENVIRONMENT=release_rehearsal SC_ALLOW_DEMO_DATA=0 DB_NAME="$db_name" python3 scripts/release/rehearsal_guard.py >/dev/null
lock="/tmp/sce-release-rehearsal-${db_name}.lock"
exec 9>"$lock"
flock -n 9 || { echo "[release.lock] FAIL lifecycle already active for $db_name" >&2; exit 75; }
exec "$@"
