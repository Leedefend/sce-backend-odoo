#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"

MODE="${PROJECT_MASTER_REPLAY_MODE:-all}"
RUN_ID="${RUN_ID:-$(date +%Y%m%dT%H%M%S)}"
ARTIFACT_ROOT="${MIGRATION_ARTIFACT_ROOT:-$ROOT_DIR/artifacts/migration/project_master_upgrade/$RUN_ID}"
ALLOWED_DBS="${MIGRATION_REPLAY_DB_ALLOWLIST:-sc_partner_acceptance,sc_migration_fresh,sc_demo}"
PROJECT_ANCHOR_EXPECTED_ROWS="${PROJECT_ANCHOR_EXPECTED_ROWS:-}"
SHELL_EXEC="$ROOT_DIR/scripts/ops/odoo_shell_exec.sh"
ADAPTER_SCRIPT="$ROOT_DIR/scripts/migration/fresh_db_project_anchor_replay_adapter.py"
WRITE_SCRIPT="$ROOT_DIR/scripts/migration/fresh_db_project_anchor_replay_write.py"
POSTCHECK_SCRIPT="$ROOT_DIR/scripts/migration/fresh_db_project_master_replay_postcheck.py"

export MIGRATION_REPO_ROOT="${MIGRATION_REPO_ROOT:-$ROOT_DIR}"
MIGRATION_REPO_ROOT_ODOO="${MIGRATION_REPO_ROOT_ODOO:-/mnt}"
if [[ -z "${MIGRATION_ARTIFACT_ROOT_ODOO:-}" ]]; then
  if [[ "$ARTIFACT_ROOT" == "$ROOT_DIR/"* ]]; then
    MIGRATION_ARTIFACT_ROOT_ODOO="$MIGRATION_REPO_ROOT_ODOO/${ARTIFACT_ROOT#"$ROOT_DIR/"}"
  else
    MIGRATION_ARTIFACT_ROOT_ODOO="$ARTIFACT_ROOT"
  fi
fi
export MIGRATION_REPLAY_DB_ALLOWLIST="$ALLOWED_DBS"
export MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT"
export PROJECT_ANCHOR_EXPECTED_ROWS

if [[ -z "${PROJECT_MASTER_REPLAY_COMPOSE_PROJECT_NAME:-}" && "${DB_NAME:-}" == "sc_partner_acceptance" ]]; then
  PROJECT_MASTER_REPLAY_COMPOSE_PROJECT_NAME="sc-backend-odoo-partner-acceptance"
fi
PROJECT_MASTER_REPLAY_COMPOSE_PROJECT_NAME="${PROJECT_MASTER_REPLAY_COMPOSE_PROJECT_NAME:-${COMPOSE_PROJECT_NAME:-}}"

if [[ "${PROJECT_MASTER_REPLAY_ALLOW_PROD:-0}" == "1" ]]; then
  guard_prod_danger
else
  guard_prod_forbid
fi

require_db_for_write_modes() {
  case "$MODE" in
    write|postcheck|all)
      : "${DB_NAME:?DB_NAME is required for PROJECT_MASTER_REPLAY_MODE=$MODE}"
      ;;
  esac
}

adapter_expected_rows() {
  python3 - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["ROOT_DIR"]) / "artifacts/migration/fresh_db_project_anchor_replay_adapter_result_v1.json"
if path.exists():
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(payload.get("replay_payload_rows") or "")
PY
}

run_adapter() {
  echo "[project.master.replay] step=adapter"
  MIGRATION_REPO_ROOT="$MIGRATION_REPO_ROOT" \
    MIGRATION_ARTIFACT_ROOT="$MIGRATION_ARTIFACT_ROOT" \
    python3 "$ADAPTER_SCRIPT"
  if [[ -z "$PROJECT_ANCHOR_EXPECTED_ROWS" ]]; then
    PROJECT_ANCHOR_EXPECTED_ROWS="$(adapter_expected_rows)"
    export PROJECT_ANCHOR_EXPECTED_ROWS
  fi
  echo "[project.master.replay] adapter_expected_rows=${PROJECT_ANCHOR_EXPECTED_ROWS:-unset}"
}

run_odoo_script() {
  local script_path="$1"
  DB_NAME="$DB_NAME" \
    COMPOSE_PROJECT_NAME="${PROJECT_MASTER_REPLAY_COMPOSE_PROJECT_NAME:-}" \
    PROJECT="${PROJECT_MASTER_REPLAY_COMPOSE_PROJECT_NAME:-}" \
    MIGRATION_REPO_ROOT="$MIGRATION_REPO_ROOT_ODOO" \
    MIGRATION_ARTIFACT_ROOT="$MIGRATION_ARTIFACT_ROOT_ODOO" \
    MIGRATION_REPLAY_DB_ALLOWLIST="$MIGRATION_REPLAY_DB_ALLOWLIST" \
    PROJECT_ANCHOR_EXPECTED_ROWS="$PROJECT_ANCHOR_EXPECTED_ROWS" \
    bash "$SHELL_EXEC" <"$script_path"
}

run_write() {
  echo "[project.master.replay] step=write db=$DB_NAME"
  run_odoo_script "$WRITE_SCRIPT"
}

run_postcheck() {
  echo "[project.master.replay] step=postcheck db=$DB_NAME"
  run_odoo_script "$POSTCHECK_SCRIPT"
}

require_db_for_write_modes
mkdir -p "$ARTIFACT_ROOT"
chmod 0777 "$ARTIFACT_ROOT" 2>/dev/null || true

echo "[project.master.replay] mode=$MODE db=${DB_NAME:-none} artifact_root=$ARTIFACT_ROOT allowlist=$MIGRATION_REPLAY_DB_ALLOWLIST compose_project=${PROJECT_MASTER_REPLAY_COMPOSE_PROJECT_NAME:-default}"

case "$MODE" in
  adapter)
    run_adapter
    ;;
  write)
    if [[ -z "$PROJECT_ANCHOR_EXPECTED_ROWS" ]]; then
      PROJECT_ANCHOR_EXPECTED_ROWS="$(adapter_expected_rows)"
      export PROJECT_ANCHOR_EXPECTED_ROWS
    fi
    run_write
    ;;
  postcheck)
    if [[ -z "$PROJECT_ANCHOR_EXPECTED_ROWS" ]]; then
      PROJECT_ANCHOR_EXPECTED_ROWS="$(adapter_expected_rows)"
      export PROJECT_ANCHOR_EXPECTED_ROWS
    fi
    run_postcheck
    ;;
  all)
    run_adapter
    run_write
    run_postcheck
    ;;
  *)
    echo "❌ unsupported PROJECT_MASTER_REPLAY_MODE=$MODE (adapter|write|postcheck|all)" >&2
    exit 2
    ;;
esac

echo "[project.master.replay] complete mode=$MODE artifact_root=$ARTIFACT_ROOT"
