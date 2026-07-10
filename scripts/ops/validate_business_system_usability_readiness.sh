#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

DB_NAME="${DB_NAME:-${DB:-sc_demo}}"
ARTIFACT_DIR="${BUSINESS_SYSTEM_READINESS_ARTIFACT_DIR:-$ROOT_DIR/artifacts/backend}"
INCLUDE_P1="${BUSINESS_SYSTEM_READINESS_INCLUDE_P1:-1}"
PROD_READONLY="${BUSINESS_SYSTEM_READINESS_PROD_READONLY:-0}"
MIGRATION_ARTIFACT_ROOT="${MIGRATION_ARTIFACT_ROOT:-/tmp/history_continuity/$DB_NAME/adhoc}"
export MIGRATION_ARTIFACT_ROOT

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"

truthy() {
  [[ "${1:-}" =~ ^(1|true|True|yes|YES)$ ]]
}

if truthy "$PROD_READONLY"; then
  if [[ "${PROD_READONLY_VERIFY:-}" != "1" ]]; then
    echo "❌ prod readonly guard: set PROD_READONLY_VERIFY=1 to run this read-only production verifier" >&2
    exit 2
  fi
  if truthy "$INCLUDE_P1"; then
    echo "❌ prod readonly readiness cannot include P1; set BUSINESS_SYSTEM_READINESS_INCLUDE_P1=0" >&2
    exit 2
  fi
else
  guard_prod_forbid
fi

: "${DB_NAME:?DB_NAME is required}"

mkdir -p "$ARTIFACT_DIR"
RUN_LOG="$(mktemp)"
SUMMARY_JSON="$ARTIFACT_DIR/business_system_usability_readiness.json"
SUMMARY_MD="$ARTIFACT_DIR/business_system_usability_readiness.md"
STARTED_AT="$(date -Iseconds)"
CHECK_FAILURES=0

cleanup() {
  rm -f "$RUN_LOG"
}
trap cleanup EXIT

run_check() {
  local name="$1"
  shift
  echo "BUSINESS_SYSTEM_READINESS_CHECK_START: ${name}"
  set +e
  (cd "$ROOT_DIR" && "$@") | tee -a "$RUN_LOG"
  local status="${PIPESTATUS[0]}"
  set -e
  if [[ "$status" -ne 0 ]]; then
    echo "BUSINESS_SYSTEM_READINESS_CHECK_FAIL: ${name} status=${status}"
    CHECK_FAILURES=1
    return 0
  fi
  echo "BUSINESS_SYSTEM_READINESS_CHECK_PASS: ${name}"
}

run_history_business_usable_probe() {
  if truthy "$PROD_READONLY"; then
    DB_NAME="$DB_NAME" MIGRATION_ARTIFACT_ROOT="$MIGRATION_ARTIFACT_ROOT" \
      bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_business_usable_probe.py
    return
  fi
  make history.business.usable.probe DB_NAME="$DB_NAME"
}

run_formal_menu_runtime_no_legacy_carrier_guard() {
  if truthy "$PROD_READONLY"; then
    python3 scripts/verify/formal_menu_no_legacy_carrier_guard.py
    DB_NAME="$DB_NAME" PROD_READONLY_VERIFY=1 \
      bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_menu_runtime_no_legacy_carrier_guard.py
    return
  fi
  make verify.formal_menu.runtime_no_legacy_carrier_guard DB_NAME="$DB_NAME"
}

run_formal_business_backfill_audit() {
  if truthy "$PROD_READONLY"; then
    DB_NAME="$DB_NAME" MIGRATION_ARTIFACT_ROOT="$MIGRATION_ARTIFACT_ROOT" \
      bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_business_backfill_audit_probe.py
    return
  fi
  make verify.formal_business_backfill.audit DB_NAME="$DB_NAME"
}

echo "BUSINESS_SYSTEM_READINESS_START: db=${DB_NAME} started_at=${STARTED_AT} include_p1=${INCLUDE_P1} prod_readonly=${PROD_READONLY}"

run_check "python_compile_readiness_inputs" \
  python3 -m py_compile \
    scripts/migration/history_business_usable_probe.py \
    scripts/verify/formal_menu_no_legacy_carrier_guard.py \
    scripts/verify/formal_menu_runtime_no_legacy_carrier_guard.py \
    scripts/verify/formal_business_backfill_audit_probe.py

if [[ "$INCLUDE_P1" == "1" || "$INCLUDE_P1" == "true" || "$INCLUDE_P1" == "yes" ]]; then
  run_check "business_capability_productization_p1" \
    make verify.business_capability.productization_p1 DB_NAME="$DB_NAME"
  P1_STATUS="PASS"
else
  P1_STATUS="SKIP"
fi

run_check "history_business_usable_probe" \
  run_history_business_usable_probe

run_check "formal_menu_runtime_no_legacy_carrier_guard" \
  run_formal_menu_runtime_no_legacy_carrier_guard

run_check "formal_business_backfill_audit" \
  run_formal_business_backfill_audit

FINISHED_AT="$(date -Iseconds)"

python3 - "$RUN_LOG" "$SUMMARY_JSON" "$SUMMARY_MD" "$DB_NAME" "$STARTED_AT" "$FINISHED_AT" "$P1_STATUS" "$CHECK_FAILURES" "$PROD_READONLY" <<'PY'
import json
import sys
from pathlib import Path

log_path = Path(sys.argv[1])
json_path = Path(sys.argv[2])
md_path = Path(sys.argv[3])
db_name = sys.argv[4]
started_at = sys.argv[5]
finished_at = sys.argv[6]
p1_status = sys.argv[7]
prod_readonly = sys.argv[9]

text = log_path.read_text(encoding="utf-8", errors="replace")


def marker(prefix):
    for line in text.splitlines():
        if line.startswith(prefix):
            raw = line.split("=", 1)[1]
            return json.loads(raw)
    return None


history = marker("HISTORY_BUSINESS_USABLE_PROBE=") or {}
formal_menu_runtime = marker("FORMAL_MENU_RUNTIME_NO_LEGACY_CARRIER_GUARD=") or {}
formal = marker("FORMAL_BUSINESS_BACKFILL_AUDIT_PROBE=") or {}

criteria = {
    "p1_productization_gate": p1_status,
    "history_business_usable_probe": history.get("status", "MISSING"),
    "formal_menu_runtime_no_legacy_carrier_guard": formal_menu_runtime.get("status", "MISSING"),
    "formal_business_backfill_audit": formal.get("status", "MISSING"),
}
shell_checks_ok = bool(int(sys.argv[8]) == 0)
ok = shell_checks_ok and all(value in {"PASS", "SKIP"} for value in criteria.values())
decision = "ready_for_business_system_use" if ok else "not_ready_for_business_system_use"

payload = {
    "scope": "business_system_usability_readiness",
    "database": db_name,
    "prod_readonly": prod_readonly in {"1", "true", "True", "yes", "YES"},
    "started_at": started_at,
    "finished_at": finished_at,
    "status": "PASS" if ok else "FAIL",
    "decision": decision,
    "shell_checks_ok": shell_checks_ok,
    "criteria": criteria,
    "history_business_usable_probe": history,
    "formal_menu_runtime_no_legacy_carrier_guard": formal_menu_runtime,
    "formal_business_backfill_audit": formal,
}

json_path.parent.mkdir(parents=True, exist_ok=True)
json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

lines = [
    "# Business System Usability Readiness",
    "",
    f"- database: `{db_name}`",
    f"- prod_readonly: `{payload['prod_readonly']}`",
    f"- status: `{payload['status']}`",
    f"- decision: `{decision}`",
    f"- started_at: `{started_at}`",
    f"- finished_at: `{finished_at}`",
    "",
    "## Criteria",
]
for key, value in criteria.items():
    lines.append(f"- {key}: `{value}`")
lines.extend(
    [
        "",
        "## Probe Summary",
        f"- history_business_usable_probe decision: `{history.get('decision', 'MISSING')}`",
        f"- history_business_usable_probe gap_count: `{history.get('gap_count', 'MISSING')}`",
        f"- formal_menu_runtime_no_legacy_carrier_guard checked_menu_count: `{formal_menu_runtime.get('checked_menu_count', 'MISSING')}`",
        f"- formal_business_backfill_audit decision: `{formal.get('decision', 'MISSING')}`",
        f"- formal_business_backfill_audit gap_count: `{formal.get('gap_count', 'MISSING')}`",
        "",
    ]
)
md_path.write_text("\n".join(lines), encoding="utf-8")

print("BUSINESS_SYSTEM_READINESS_SUMMARY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if not ok:
    raise SystemExit(2)
PY

echo "BUSINESS_SYSTEM_READINESS_RESULT: PASS db=${DB_NAME} started_at=${STARTED_AT} finished_at=${FINISHED_AT}"
