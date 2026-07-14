#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
PIDFILE="${FRONTEND_ACCEPTANCE_PIDFILE:-/tmp/sc-frontend-acceptance.pid}"
LOGFILE="${FRONTEND_ACCEPTANCE_LOGFILE:-/tmp/sc-frontend-acceptance.log}"
PORT="${FRONTEND_ACCEPTANCE_PORT:-5175}"
if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "[frontend.acceptance.up] already running pid=$(cat "$PIDFILE") port=$PORT db=sc_frontend_acceptance"
  exit 0
fi
rm -f "$PIDFILE"
(
  cd "$ROOT_DIR"
  export VITE_API_PROXY_TARGET="${VITE_API_PROXY_TARGET:-http://127.0.0.1:8070}"
  export VITE_ODOO_DB=sc_frontend_acceptance VITE_ODOO_DB_LOCKED=1 VITE_APP_ENV=acceptance
  exec scripts/dev/pnpm_exec.sh -C frontend/apps/web dev --host 127.0.0.1 --port "$PORT"
) >"$LOGFILE" 2>&1 &
echo $! >"$PIDFILE"
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT}/login" >/dev/null 2>&1; then
    echo "[frontend.acceptance.up] PASS url=http://127.0.0.1:${PORT} db=sc_frontend_acceptance"
    exit 0
  fi
  sleep 1
done
echo "[frontend.acceptance.up] FAIL; see $LOGFILE" >&2
exit 1
