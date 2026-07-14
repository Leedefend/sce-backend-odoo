#!/usr/bin/env bash
set -euo pipefail
PIDFILE="${FRONTEND_ACCEPTANCE_PIDFILE:-/tmp/sc-frontend-acceptance.pid}"
if [[ -f "$PIDFILE" ]]; then
  pid="$(cat "$PIDFILE")"
  kill "$pid" 2>/dev/null || true
  rm -f "$PIDFILE"
fi
echo "[frontend.acceptance.down] PASS"
