#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARTIFACT_DIR="${BUSINESS_BROWSER_ARTIFACT_DIR:-${ROOT_DIR}/artifacts/browser-real-user-business-closure/current}"
mkdir -p "$ARTIFACT_DIR"
chmod 0777 "$ARTIFACT_DIR"
rm -f "$ARTIFACT_DIR"/browser_error.json "$ARTIFACT_DIR"/browser_summary.json "$ARTIFACT_DIR"/backend_assert.json

cleanup() {
  DB_NAME="${DB_NAME:?}" bash "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" < "$ROOT_DIR/scripts/verify/business_real_user_browser_cleanup.py" || true
}

trap cleanup EXIT

DB_NAME="${DB_NAME:?}" bash "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" < "$ROOT_DIR/scripts/verify/business_real_user_browser_setup.py"
(
  cd "$ROOT_DIR/frontend/apps/web"
  BUSINESS_BROWSER_ARTIFACT_DIR="$ARTIFACT_DIR" FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:5174}" DB_NAME="${DB_NAME:?}" BROWSER_CLOSURE_ACTION="${BROWSER_CLOSURE_ACTION:-approve}" node "$ROOT_DIR/scripts/verify/business_real_user_browser_closure.js"
)
DB_NAME="${DB_NAME:?}" bash "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" < "$ROOT_DIR/scripts/verify/business_real_user_browser_assert.py"

echo "BUSINESS_REAL_USER_BROWSER_CLOSURE=PASS action=${BROWSER_CLOSURE_ACTION:-approve}"
echo "ARTIFACT_DIR=$ARTIFACT_DIR"
