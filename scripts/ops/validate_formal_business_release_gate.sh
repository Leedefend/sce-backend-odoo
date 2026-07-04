#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

DB_NAME="${DB_NAME:-${DB:-sc_demo}}"
USER_CONFIRMED_ALIGNMENT_RECORD_LIMIT="${USER_CONFIRMED_ALIGNMENT_RECORD_LIMIT:-50}"

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME is required}"

ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH:-/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux}"
DB_PASSWORD="${DB_PASSWORD:-${DB_USER}}"

run_odoo_shell_check() {
  local name="$1"
  local script="$2"
  local output_file
  output_file="$(mktemp)"
  echo "FORMAL_BUSINESS_RELEASE_GATE_CHECK_START: ${name}"
  compose_dev exec -T \
    -e PYTHONWARNINGS=ignore \
    -e USER_CONFIRMED_ALIGNMENT_RECORD_LIMIT="$USER_CONFIRMED_ALIGNMENT_RECORD_LIMIT" \
    odoo odoo shell -d "$DB_NAME" \
    --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
    --addons-path="$ODOO_ADDONS_PATH" \
    --logfile=/dev/null --log-level=warn \
    < "$ROOT_DIR/$script" | tee "$output_file"
  local child_status="${PIPESTATUS[0]}"
  if [[ "$child_status" -ne 0 ]]; then
    rm -f "$output_file"
    return "$child_status"
  fi
  local summary_status
  summary_status="$(
    python3 - "$output_file" <<'PY'
import json
import sys

status = ""
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    for raw in handle:
        line = raw.strip()
        if not line:
            continue
        if not line.startswith("{") and "={" in line:
            line = line[line.index("={") + 1:]
        if not line.startswith("{") or '"status"' not in line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        status = payload.get("status") or status
print(status)
PY
  )"
  rm -f "$output_file"
  if [[ "$summary_status" != "PASS" ]]; then
    echo "FORMAL_BUSINESS_RELEASE_GATE_CHECK_FAIL: ${name} status=${summary_status:-missing}"
    return 1
  fi
  echo "FORMAL_BUSINESS_RELEASE_GATE_CHECK_PASS: ${name}"
}

run_odoo_shell_audit_report() {
  local name="$1"
  local script="$2"
  echo "FORMAL_BUSINESS_RELEASE_GATE_AUDIT_START: ${name}"
  compose_dev exec -T \
    -e PYTHONWARNINGS=ignore \
    -e USER_CONFIRMED_ALIGNMENT_RECORD_LIMIT="$USER_CONFIRMED_ALIGNMENT_RECORD_LIMIT" \
    odoo odoo shell -d "$DB_NAME" \
    --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
    --addons-path="$ODOO_ADDONS_PATH" \
    --logfile=/dev/null --log-level=warn \
    < "$ROOT_DIR/$script"
  echo "FORMAL_BUSINESS_RELEASE_GATE_AUDIT_REPORTED: ${name}"
}

started_at="$(date -Iseconds)"
echo "FORMAL_BUSINESS_RELEASE_GATE_START: db=${DB_NAME} started_at=${started_at}"

run_odoo_shell_check "user_confirmed_menu_surface" "scripts/verify/user_confirmed_menu_surface_guard.py"
run_odoo_shell_check "formal_action_runtime_drift" "scripts/verify/formal_action_runtime_drift_audit.py"
run_odoo_shell_check "engineering_progress_income_visible_contract" "scripts/verify/engineering_progress_income_visible_contract_audit.py"
run_odoo_shell_check "formal_entry_metadata" "scripts/verify/formal_entry_metadata_audit.py"
run_odoo_shell_check "user_confirmed_form_capability" "scripts/verify/user_confirmed_form_capability_audit.py"
run_odoo_shell_audit_report "user_confirmed_form_data_alignment" "scripts/verify/user_confirmed_form_data_alignment_audit.py"
run_odoo_shell_check "user_confirmed_settlement_usability" "scripts/verify/user_confirmed_settlement_usability_audit.py"
run_odoo_shell_check "project_budget_legacy_material" "scripts/verify/project_budget_legacy_material_audit.py"
run_odoo_shell_check "operation_strategy_contract_surface" "scripts/verify/operation_strategy_contract_surface_audit.py"
run_odoo_shell_check "receipt_invoice_source_document" "scripts/verify/receipt_invoice_source_document_audit.py"
run_odoo_shell_check "settlement_contract_surface" "scripts/verify/settlement_contract_surface_audit.py"
run_odoo_shell_check "material_plan_visible_note" "scripts/verify/material_plan_visible_note_audit.py"
run_odoo_shell_check "material_rfq_source_coverage" "scripts/verify/material_rfq_source_coverage_audit.py"
run_odoo_shell_check "construction_diary_visible_fields" "scripts/verify/construction_diary_visible_fields_audit.py"
run_odoo_shell_check "full_product_capability_scope" "scripts/verify/full_product_capability_scope_audit.py"
run_odoo_shell_check "formal_business_operation_capability_matrix" "scripts/verify/formal_business_operation_capability_matrix.py"
run_odoo_shell_check "formal_business_operation_core_flow_smoke" "scripts/verify/formal_business_operation_core_flow_smoke.py"

echo "FORMAL_BUSINESS_RELEASE_GATE_CHECK_START: business_capability"
DB_NAME="$DB_NAME" "$ROOT_DIR/scripts/ops/validate_business_capability_gate.sh"
echo "FORMAL_BUSINESS_RELEASE_GATE_CHECK_PASS: business_capability"

echo "FORMAL_BUSINESS_RELEASE_GATE_CHECK_START: business_capability_productization_p1"
DB_NAME="$DB_NAME" "$ROOT_DIR/scripts/ops/validate_business_capability_productization_p1.sh"
echo "FORMAL_BUSINESS_RELEASE_GATE_CHECK_PASS: business_capability_productization_p1"

finished_at="$(date -Iseconds)"
echo "FORMAL_BUSINESS_RELEASE_GATE_RESULT: PASS db=${DB_NAME} started_at=${started_at} finished_at=${finished_at}"
