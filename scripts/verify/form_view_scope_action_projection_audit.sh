#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

DB_NAME="${DB_NAME:-sc_demo}"
CONTAINER="${ODOO_CONTAINER:-sc-backend-odoo-dev-odoo-1}"
OUT_DIR="${OUT_DIR:-docs/audit/native/form_view_scope_action_projection}"
TMP_SCRIPT="/tmp/form_view_scope_action_projection_audit.py"
TMP_OUT="/tmp/form_view_scope_action_projection"
LIMIT="${LIMIT:-${FORM_VIEW_SCOPE_ACTION_LIMIT:-30}}"
AUDIT_LOGIN="${FORM_VIEW_SCOPE_AUDIT_LOGIN:-${E2E_LOGIN:-wutao}}"

docker cp scripts/verify/form_view_scope_action_projection_audit.py "$CONTAINER:$TMP_SCRIPT"

ENV=dev \
ENV_FILE=.env.dev \
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-sc-backend-odoo-dev}" \
PROJECT="${PROJECT:-sc-backend-odoo-dev}" \
DB_NAME="$DB_NAME" \
bash scripts/ops/odoo_shell_exec.sh <<PY
import runpy
import sys
sys.argv = [
    "$TMP_SCRIPT",
    "--out-dir",
    "$TMP_OUT",
    "--limit",
    "$LIMIT",
    "--audit-login",
    "$AUDIT_LOGIN",
]
runpy.run_path("$TMP_SCRIPT", run_name="__main__", init_globals={"env": env})
PY

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"
docker cp "$CONTAINER:$TMP_OUT/." "$OUT_DIR/"
echo "form view action projection audit written to $OUT_DIR"
