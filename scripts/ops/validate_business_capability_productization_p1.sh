#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

DB_NAME="${DB_NAME:-${DB:-sc_demo}}"

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME is required}"

run_static_check() {
  local name="$1"
  shift
  echo "BUSINESS_CAPABILITY_PRODUCTIZATION_P1_CHECK_START: ${name}"
  (cd "$ROOT_DIR" && "$@")
  echo "BUSINESS_CAPABILITY_PRODUCTIZATION_P1_CHECK_PASS: ${name}"
}

run_odoo_shell_check() {
  local name="$1"
  local script="$2"
  echo "BUSINESS_CAPABILITY_PRODUCTIZATION_P1_CHECK_START: ${name}"
  DB_NAME="$DB_NAME" MIGRATION_ARTIFACT_ROOT="${MIGRATION_ARTIFACT_ROOT:-}" \
    bash "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" < "$ROOT_DIR/$script"
  echo "BUSINESS_CAPABILITY_PRODUCTIZATION_P1_CHECK_PASS: ${name}"
}

run_odoo_shell_json_artifact_check() {
  local name="$1"
  local script="$2"
  local artifact="$3"
  local scope="$4"
  local output_file
  output_file="$(mktemp)"
  echo "BUSINESS_CAPABILITY_PRODUCTIZATION_P1_CHECK_START: ${name}"
  DB_NAME="$DB_NAME" MIGRATION_ARTIFACT_ROOT="${MIGRATION_ARTIFACT_ROOT:-}" \
    bash "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" < "$ROOT_DIR/$script" | tee "$output_file"
  local child_status="${PIPESTATUS[0]}"
  if [[ "$child_status" -ne 0 ]]; then
    rm -f "$output_file"
    return "$child_status"
  fi
  python3 - "$output_file" "$ROOT_DIR/$artifact" "$scope" <<'PY'
import json
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
target = Path(sys.argv[2])
scope = sys.argv[3]
decoder = json.JSONDecoder()
match = None
for index, char in enumerate(source):
    if char != "{":
        continue
    try:
        payload, _ = decoder.raw_decode(source[index:])
    except json.JSONDecodeError:
        continue
    if isinstance(payload, dict) and payload.get("scope") == scope:
        match = payload
if not match:
    raise SystemExit(f"missing json artifact payload for scope={scope}")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(match, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
PY
  rm -f "$output_file"
  echo "BUSINESS_CAPABILITY_PRODUCTIZATION_P1_CHECK_PASS: ${name}"
}

started_at="$(date -Iseconds)"
echo "BUSINESS_CAPABILITY_PRODUCTIZATION_P1_START: db=${DB_NAME} started_at=${started_at}"

run_static_check "python_compile_productization_guards" \
  python3 -m py_compile \
    scripts/verify/user_business_data_portrait.py \
    scripts/verify/user_business_productization_baseline_guard.py \
    scripts/verify/user_confirmed_62_business_entry_integration_matrix.py \
    scripts/verify/user_confirmed_menu_surface_guard.py \
    scripts/verify/locked_fact_formal_model_continuity_guard.py \
    scripts/verify/p1_locked_fact_mapping_candidate_guard.py \
    scripts/verify/p1_locked_fact_mapping_candidate_probe.py \
    scripts/verify/p1_relationship_suggestion_audit.py \
    scripts/verify/p1_relationship_review_queue_audit.py \
    scripts/verify/finance_interfund_handling_entry_audit.py \
    scripts/verify/p1_daily_business_form_usability_audit.py \
    scripts/verify/p1_formal_relationship_continuity_audit.py \
    scripts/verify/p1_formal_relationship_scope_block_smoke.py \
    scripts/verify/user_data_product_field_coverage_matrix.py \
    scripts/verify/industry_module_handling_capability_boundary_audit.py \
    scripts/verify/finance_business_fact_projection_audit.py \
    scripts/verify/finance_business_project_summary_audit.py \
    scripts/verify/interfund_movement_project_summary_audit.py \
    scripts/verify/finance_project_capital_position_audit.py \
    scripts/verify/finance_project_counterparty_position_audit.py \
    scripts/verify/finance_counterparty_position_summary_audit.py
run_static_check "user_confirmed_62_business_entry_integration_matrix" \
  python3 scripts/verify/user_confirmed_62_business_entry_integration_matrix.py
run_odoo_shell_json_artifact_check "user_business_data_portrait" \
  scripts/verify/user_business_data_portrait.py \
  "artifacts/user_business_data_portrait.${DB_NAME}.json" \
  real_user_business_data_portrait
run_static_check "user_business_productization_baseline_guard" \
  python3 scripts/verify/user_business_productization_baseline_guard.py

run_static_check "user_data_product_field_coverage_matrix" \
  make verify.user_data.product_field_coverage.matrix DB_NAME="$DB_NAME"
run_static_check "industry_module_handling_capability_boundary" \
  make verify.industry_module.handling_capability_boundary DB_NAME="$DB_NAME"

run_odoo_shell_check "user_confirmed_menu_surface_guard" \
  scripts/verify/user_confirmed_menu_surface_guard.py
run_odoo_shell_check "locked_fact_formal_model_continuity_guard" \
  scripts/verify/locked_fact_formal_model_continuity_guard.py
run_odoo_shell_check "finance_interfund_handling_entry_audit" \
  scripts/verify/finance_interfund_handling_entry_audit.py
run_static_check "p1_daily_business_form_usability_audit" \
  env \
    P1_DAILY_BUSINESS_FORM_USABILITY_AUDIT_JSON=/tmp/sce-product-artifacts/p1_daily_business_form_usability_audit.json \
    P1_DAILY_BUSINESS_FORM_USABILITY_AUDIT_MD=/tmp/sce-product-artifacts/p1_daily_business_form_usability_audit.md \
    python3 scripts/verify/p1_daily_business_form_usability_audit.py
run_odoo_shell_json_artifact_check "p1_locked_fact_mapping_candidate_probe" \
  scripts/verify/p1_locked_fact_mapping_candidate_probe.py \
  "artifacts/p1_locked_fact_mapping_candidate_probe.${DB_NAME}.json" \
  "p1_locked_fact_mapping_candidate_probe"
run_static_check "p1_locked_fact_mapping_candidate_guard" \
  python3 scripts/verify/p1_locked_fact_mapping_candidate_guard.py
run_odoo_shell_check "p1_relationship_suggestion_audit" \
  scripts/verify/p1_relationship_suggestion_audit.py
run_odoo_shell_check "p1_relationship_review_queue_audit" \
  scripts/verify/p1_relationship_review_queue_audit.py
run_odoo_shell_check "p1_formal_relationship_continuity_audit" \
  scripts/verify/p1_formal_relationship_continuity_audit.py
run_odoo_shell_check "p1_formal_relationship_scope_block_smoke" \
  scripts/verify/p1_formal_relationship_scope_block_smoke.py

run_odoo_shell_check "finance_business_fact_projection_audit" \
  scripts/verify/finance_business_fact_projection_audit.py
run_odoo_shell_check "finance_business_project_summary_audit" \
  scripts/verify/finance_business_project_summary_audit.py
run_odoo_shell_check "interfund_movement_project_summary_audit" \
  scripts/verify/interfund_movement_project_summary_audit.py
run_odoo_shell_check "finance_project_capital_position_audit" \
  scripts/verify/finance_project_capital_position_audit.py
run_odoo_shell_check "finance_project_counterparty_position_audit" \
  scripts/verify/finance_project_counterparty_position_audit.py
run_odoo_shell_check "finance_counterparty_position_summary_audit" \
  scripts/verify/finance_counterparty_position_summary_audit.py

finished_at="$(date -Iseconds)"
echo "BUSINESS_CAPABILITY_PRODUCTIZATION_P1_RESULT: PASS db=${DB_NAME} started_at=${started_at} finished_at=${finished_at}"
