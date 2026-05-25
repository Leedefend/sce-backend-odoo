#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"

: "${DB_NAME:?DB_NAME is required}"

if [[ "${HISTORY_CONTINUITY_ALLOW_PROD:-0}" == "1" ]]; then
  guard_prod_danger
else
  guard_prod_forbid
fi

MODE="${HISTORY_CONTINUITY_MODE:-rehearse}"
RUN_ID="${RUN_ID:-$(date +%Y%m%dT%H%M%S)}"
ALLOWED_DBS="${MIGRATION_REPLAY_DB_ALLOWLIST:-sc_migration_fresh,sc_demo}"
ARTIFACT_ROOT="${MIGRATION_ARTIFACT_ROOT:-/tmp/history_continuity/${DB_NAME}/${RUN_ID}}"
START_AT="${HISTORY_CONTINUITY_START_AT:-}"
STOP_AFTER="${HISTORY_CONTINUITY_STOP_AFTER:-}"
export MIGRATION_REPO_ROOT="${MIGRATION_REPO_ROOT:-$ROOT_DIR}"
MIGRATION_REPO_ROOT_ODOO="${MIGRATION_REPO_ROOT_ODOO:-/mnt}"
MIGRATION_ARTIFACT_ROOT_ODOO="${MIGRATION_ARTIFACT_ROOT_ODOO:-$ARTIFACT_ROOT}"
export MIGRATION_REPLAY_DB_ALLOWLIST="$ALLOWED_DBS"
export MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT"

SHELL_EXEC="$ROOT_DIR/scripts/ops/odoo_shell_exec.sh"
PRECHECK_SCRIPT="$ROOT_DIR/scripts/migration/fresh_db_replay_payload_precheck.py"
PROBE_SCRIPT="$ROOT_DIR/scripts/migration/history_continuity_usability_probe.py"
USER_REBUILD="$ROOT_DIR/scripts/migration/user_history_rebuild.sh"
REAL_USER_NORMALIZE_SCRIPT="$ROOT_DIR/scripts/migration/history_real_user_normalize_write.py"
USER_VISIBLE_SURFACE_OVERLAY_SCRIPT="$ROOT_DIR/scripts/migration/legacy_user_visible_surface_overlay_write.py"
USER_PROFILE_RUNTIME_PROJECTION_SCRIPT="$ROOT_DIR/scripts/migration/history_user_profile_runtime_projection_write.py"
USER_ACCESS_PROJECTION_SCRIPT="$ROOT_DIR/scripts/migration/history_legacy_user_access_projection_write.py"
CONTRACT_COUNTERPARTY_ADAPTER="$ROOT_DIR/scripts/migration/fresh_db_contract_counterparty_partner_replay_adapter.py"
RECEIPT_COUNTERPARTY_ADAPTER="$ROOT_DIR/scripts/migration/fresh_db_receipt_counterparty_partner_replay_adapter.py"
CONTRACT_LINE_ADAPTER="$ROOT_DIR/scripts/migration/fresh_db_contract_line_replay_adapter.py"
SUPPLIER_CONTRACT_ADAPTER="$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_replay_adapter.py"
SUPPLIER_CONTRACT_LINE_ADAPTER="$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_line_replay_adapter.py"
INCLUDE_BLOCKED_GROUP_B="${HISTORY_CONTINUITY_INCLUDE_BLOCKED_GROUP_B:-0}"
INCLUDE_DETAIL_FACTS="${HISTORY_CONTINUITY_INCLUDE_DETAIL_FACTS:-1}"
INCLUDE_PAYMENT_STATE_RECOVERY="${HISTORY_CONTINUITY_INCLUDE_PAYMENT_STATE_RECOVERY:-0}"
INCLUDE_PROJECT_LIFECYCLE_CONTINUITY="${HISTORY_CONTINUITY_INCLUDE_PROJECT_LIFECYCLE_CONTINUITY:-0}"
INCLUDE_MATERIAL_CATALOG="${HISTORY_CONTINUITY_INCLUDE_MATERIAL_CATALOG:-1}"
INCLUDE_FILE_INDEX="${HISTORY_CONTINUITY_INCLUDE_FILE_INDEX:-1}"
INCLUDE_ATTENDANCE_CHECKIN="${HISTORY_CONTINUITY_INCLUDE_ATTENDANCE_CHECKIN:-0}"
INCLUDE_PERSONNEL_MOVEMENT="${HISTORY_CONTINUITY_INCLUDE_PERSONNEL_MOVEMENT:-0}"
INCLUDE_SALARY_LINE="${HISTORY_CONTINUITY_INCLUDE_SALARY_LINE:-0}"
INCLUDE_USER_VISIBLE_SURFACE_OVERLAY="${HISTORY_CONTINUITY_INCLUDE_USER_VISIBLE_SURFACE_OVERLAY:-1}"
INCLUDE_FORMAL_PROJECTIONS="${HISTORY_CONTINUITY_INCLUDE_FORMAL_PROJECTIONS:-1}"
USE_PACKAGED_PAYLOADS="${HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS:-0}"
MATERIALIZED_FILES=()

cleanup_materialized_files() {
  local path
  for path in "${MATERIALIZED_FILES[@]:-}"; do
    if [[ -n "$path" && -f "$path" ]]; then
      rm -f "$path"
    fi
  done
}
trap cleanup_materialized_files EXIT

run_odoo_script() {
  local script_path="$1"
  DB_NAME="$DB_NAME" \
  MIGRATION_REPO_ROOT="$MIGRATION_REPO_ROOT_ODOO" \
  MIGRATION_REPLAY_DB_ALLOWLIST="$MIGRATION_REPLAY_DB_ALLOWLIST" \
  MIGRATION_ARTIFACT_ROOT="$MIGRATION_ARTIFACT_ROOT_ODOO" \
  bash "$SHELL_EXEC" <"$script_path"
}

run_odoo_write_script() {
  local script_path="$1"
  DB_NAME="$DB_NAME" \
  MIGRATION_REPO_ROOT="$MIGRATION_REPO_ROOT_ODOO" \
  MIGRATION_REPLAY_DB_ALLOWLIST="$MIGRATION_REPLAY_DB_ALLOWLIST" \
  MIGRATION_ARTIFACT_ROOT="$MIGRATION_ARTIFACT_ROOT_ODOO" \
  MIGRATION_WRITE_MODE=write \
  bash "$SHELL_EXEC" <"$script_path"
}

run_python_validator() {
  local script_path="$1"
  MIGRATION_REPO_ROOT="$MIGRATION_REPO_ROOT" \
  MIGRATION_ARTIFACT_ROOT="$MIGRATION_ARTIFACT_ROOT" \
  python3 "$script_path"
}

materialize_xml_parts() {
  local target="$1"
  local parts_dir="${target}.parts"
  if [[ -f "$target" ]]; then
    return 0
  fi
  if [[ ! -d "$parts_dir" ]]; then
    echo "❌ missing xml and parts dir: $target" >&2
    exit 2
  fi
  echo "[history.continuity] materialize xml parts: $target"
  cat "$parts_dir"/part-*.part >"$target"
  MATERIALIZED_FILES+=("$target")
}

run_legacy_workflow_audit_adapter() {
  materialize_xml_parts "$ROOT_DIR/migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_workflow_audit_replay_adapter.py"
}

run_payment_request_outflow_state_activation_adapter() {
  materialize_xml_parts "$ROOT_DIR/migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml"
  python3 "$ROOT_DIR/scripts/migration/history_payment_request_outflow_state_activation_adapter.py"
}

packaged_payload_path_for_step() {
  local step_name="$1"
  case "$step_name" in
    payment_request_outflow_state_activation_adapter)
      printf '%s\n' "$ROOT_DIR/artifacts/migration/history_payment_request_outflow_state_activation_payload_v1.csv"
      ;;
    payment_request_outflow_approved_recovery_adapter)
      printf '%s\n' "$ROOT_DIR/artifacts/migration/history_payment_request_outflow_approved_recovery_payload_v1.csv"
      ;;
    payment_request_outflow_done_recovery_adapter)
      printf '%s\n' "$ROOT_DIR/artifacts/migration/history_payment_request_outflow_done_recovery_payload_v1.csv"
      ;;
    *)
      printf '\n'
      ;;
  esac
}

STEP_ACTIVE=1
if [[ -n "$START_AT" ]]; then
  STEP_ACTIVE=0
fi

run_step() {
  local step_name="$1"
  shift
  if [[ "$STEP_ACTIVE" != "1" ]]; then
    if [[ "$step_name" == "$START_AT" ]]; then
      STEP_ACTIVE=1
    else
      echo "[history.continuity] skip step=$step_name start_at=$START_AT"
      return 0
    fi
  fi
  echo "[history.continuity] step=$step_name"
  if [[ "$USE_PACKAGED_PAYLOADS" == "1" && "$step_name" == *_adapter ]]; then
    local packaged_payload_path
    packaged_payload_path="$(packaged_payload_path_for_step "$step_name")"
    if [[ -z "$packaged_payload_path" || -f "$packaged_payload_path" ]]; then
      echo "[history.continuity] skip adapter step=$step_name by HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1"
      if [[ -n "$STOP_AFTER" && "$step_name" == "$STOP_AFTER" ]]; then
        echo "[history.continuity] stop after step=$step_name"
        exit 0
      fi
      return 0
    fi
    echo "[history.continuity] run adapter step=$step_name because packaged payload is missing: $packaged_payload_path"
  fi
  "$@"
  if [[ -n "$STOP_AFTER" && "$step_name" == "$STOP_AFTER" ]]; then
    echo "[history.continuity] stop after step=$step_name"
    exit 0
  fi
}

echo "[history.continuity] mode=$MODE db=$DB_NAME artifact_root=$ARTIFACT_ROOT packaged_payloads=$USE_PACKAGED_PAYLOADS"

case "$MODE" in
  rehearse)
    run_step manifest_dry_run run_python_validator "$ROOT_DIR/scripts/migration/fresh_db_replay_runner_dry_run.py"
    run_step user_asset_verify python3 "$ROOT_DIR/scripts/migration/user_asset_verify.py" --asset-root "$ROOT_DIR/migration_assets" --lane user --check
    run_step replay_payload_precheck run_odoo_script "$PRECHECK_SCRIPT"
    run_step usability_probe run_odoo_script "$PROBE_SCRIPT"
    ;;
  replay)
    run_step user_rebuild bash -c "DB_NAME=\"$DB_NAME\" MIGRATION_REPO_ROOT=\"$MIGRATION_REPO_ROOT\" MIGRATION_ARTIFACT_ROOT=\"$MIGRATION_ARTIFACT_ROOT\" bash \"$USER_REBUILD\""
    run_step legacy_user_context_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_user_context_replay_adapter.py"
    run_step legacy_user_context_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_user_context_replay_write.py"
    run_step real_user_normalize run_odoo_script "$REAL_USER_NORMALIZE_SCRIPT"
    if [[ "$INCLUDE_USER_VISIBLE_SURFACE_OVERLAY" == "1" ]]; then
      run_step legacy_user_visible_surface_overlay run_odoo_script "$USER_VISIBLE_SURFACE_OVERLAY_SCRIPT"
    else
      echo "[history.continuity] skip legacy user visible surface overlay by HISTORY_CONTINUITY_INCLUDE_USER_VISIBLE_SURFACE_OVERLAY=0"
    fi
    run_step legacy_user_profile_runtime_projection run_odoo_script "$USER_PROFILE_RUNTIME_PROJECTION_SCRIPT"
    run_step legacy_user_project_scope_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_user_project_scope_replay_adapter.py"
    run_step legacy_user_project_scope_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_user_project_scope_replay_write.py"
    run_step legacy_task_evidence_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_task_evidence_replay_adapter.py"
    run_step legacy_task_evidence_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_task_evidence_replay_write.py"
    if [[ "$INCLUDE_ATTENDANCE_CHECKIN" == "1" ]]; then
      run_step legacy_attendance_checkin_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_attendance_checkin_replay_adapter.py"
      run_step legacy_attendance_checkin_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_attendance_checkin_replay_write.py"
    else
      echo "[history.continuity] skip privacy-restricted attendance check-in by HISTORY_CONTINUITY_INCLUDE_ATTENDANCE_CHECKIN=0"
    fi
    if [[ "$INCLUDE_PERSONNEL_MOVEMENT" == "1" ]]; then
      run_step legacy_personnel_movement_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_personnel_movement_replay_adapter.py"
      run_step legacy_personnel_movement_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_personnel_movement_replay_write.py"
    else
      echo "[history.continuity] skip privacy-restricted personnel movement by HISTORY_CONTINUITY_INCLUDE_PERSONNEL_MOVEMENT=0"
    fi
    if [[ "$INCLUDE_SALARY_LINE" == "1" ]]; then
      run_step legacy_salary_line_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_salary_line_replay_adapter.py"
      run_step legacy_salary_line_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_salary_line_replay_write.py"
    else
      echo "[history.continuity] skip privacy-restricted salary line by HISTORY_CONTINUITY_INCLUDE_SALARY_LINE=0"
    fi
    run_step replay_payload_precheck run_odoo_script "$PRECHECK_SCRIPT"
    run_step partner_l4_anchor_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_partner_l4_replay_write.py"
    run_step project_anchor_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_project_anchor_replay_write.py"
    run_step legacy_user_access_projection run_odoo_script "$USER_ACCESS_PROJECTION_SCRIPT"
    run_step legacy_account_master_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_account_master_replay_adapter.py"
    run_step legacy_account_master_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_account_master_replay_write.py"
    run_step legacy_account_transaction_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_account_transaction_replay_adapter.py"
    run_step legacy_account_transaction_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_account_transaction_replay_write.py"
    if [[ "$INCLUDE_MATERIAL_CATALOG" == "1" ]]; then
      run_step legacy_material_catalog_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_material_catalog_replay_adapter.py"
      run_step legacy_material_catalog_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_material_catalog_replay_write.py"
      run_step legacy_tender_registration_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_tender_registration_replay_adapter.py"
      run_step legacy_tender_registration_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_tender_registration_replay_write.py"
      run_step legacy_material_stock_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_material_stock_replay_adapter.py"
      run_step legacy_material_stock_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_material_stock_replay_write.py"
      run_step legacy_labor_subcontract_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_labor_subcontract_replay_adapter.py"
      run_step legacy_labor_subcontract_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_labor_subcontract_replay_write.py"
      run_step legacy_equipment_lease_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_equipment_lease_replay_adapter.py"
      run_step legacy_equipment_lease_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_equipment_lease_replay_write.py"
    else
      echo "[history.continuity] skip legacy material catalog by HISTORY_CONTINUITY_INCLUDE_MATERIAL_CATALOG=0"
    fi
    if [[ "$INCLUDE_FILE_INDEX" == "1" ]]; then
      run_step legacy_file_index_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_file_index_replay_adapter.py"
      run_step legacy_file_index_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_file_index_replay_write.py"
    else
      echo "[history.continuity] skip legacy file index by HISTORY_CONTINUITY_INCLUDE_FILE_INDEX=0"
    fi
    run_step contract_counterparty_partner_adapter python3 "$CONTRACT_COUNTERPARTY_ADAPTER"
    run_step contract_counterparty_partner_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_counterparty_partner_replay_write.py"
    run_step receipt_counterparty_partner_adapter python3 "$RECEIPT_COUNTERPARTY_ADAPTER"
    run_step receipt_counterparty_partner_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_counterparty_partner_replay_write.py"
    run_step project_member_neutral_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_project_member_neutral_replay_adapter.py"
    run_step project_member_neutral_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_project_member_neutral_replay_write.py"
    run_step contract_header_remaining_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_contract_remaining_adapter.py"
    run_step contract_header_completed_1332 run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_remaining_write.py"
    if [[ -f "$ROOT_DIR/migration_assets/20_business/contract/contract_header_v1.xml" ]]; then
      echo "[history.continuity] skip legacy contract supplemental slices because contract_header_v1.xml replay is authoritative"
    else
      run_step contract_missing_partner_anchors run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_missing_partner_anchor_write.py"
      run_step contract_12_missing_partner_anchors run_odoo_script "$ROOT_DIR/scripts/migration/contract_12_row_missing_partner_anchor_write.py"
      run_step contract_header_special_12 run_odoo_script "$ROOT_DIR/scripts/migration/contract_12_row_create_only_write.py"
      run_step contract_header_retry_57 run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_57_retry_write.py"
    fi
    if [[ -f "$ROOT_DIR/migration_assets/20_business/contract/contract_header_v1.xml" ]]; then
      echo "[history.continuity] skip legacy contract recovery lanes because contract_header_v1.xml replay is authoritative"
    else
      run_step contract_unreached_ready_adapter python3 "$ROOT_DIR/scripts/migration/history_contract_unreached_ready_replay_adapter.py"
      run_step contract_unreached_ready_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_contract_unreached_ready_replay_write.py"
      run_step partner_master_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_partner_master_targeted_replay_adapter.py"
      run_step partner_master_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_partner_master_targeted_replay_write.py"
      run_step contract_partner_recovery_adapter python3 "$ROOT_DIR/scripts/migration/history_contract_partner_recovery_adapter.py"
      run_step contract_partner_recovery_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_contract_partner_recovery_write.py"
    fi
    run_step legacy_purchase_contract_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_purchase_contract_replay_adapter.py"
    run_step legacy_purchase_contract_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_purchase_contract_replay_write.py"
    if [[ -f "$ROOT_DIR/migration_assets/20_business/contract/contract_header_v1.xml" ]]; then
      echo "[history.continuity] skip legacy contract direction recovery lanes because contract_header_v1.xml replay is authoritative"
    else
      run_step partner_master_direction_defer_adapter python3 "$ROOT_DIR/scripts/migration/history_partner_master_direction_defer_replay_adapter.py"
      run_step partner_master_direction_defer_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_partner_master_direction_defer_replay_write.py"
      run_step contract_direction_defer_recovery_adapter python3 "$ROOT_DIR/scripts/migration/history_contract_direction_defer_recovery_adapter.py"
      run_step contract_direction_defer_recovery_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_contract_direction_defer_recovery_write.py"
    fi
    if [[ "$INCLUDE_DETAIL_FACTS" == "1" ]]; then
      run_step contract_line_adapter python3 "$CONTRACT_LINE_ADAPTER"
      run_step contract_line_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_line_replay_write.py"
      run_step supplier_contract_adapter python3 "$SUPPLIER_CONTRACT_ADAPTER"
      run_step supplier_partner_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_supplier_partner_targeted_replay_adapter.py"
      run_step supplier_partner_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_supplier_partner_targeted_replay_write.py"
      run_step supplier_contract_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_replay_write.py"
      run_step supplier_contract_line_adapter python3 "$SUPPLIER_CONTRACT_LINE_ADAPTER"
      run_step supplier_contract_line_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_line_replay_write.py"
    else
      echo "[history.continuity] skip detail fact lanes by HISTORY_CONTINUITY_INCLUDE_DETAIL_FACTS=0"
      if [[ "$INCLUDE_BLOCKED_GROUP_B" == "1" ]]; then
        echo "[history.continuity] HISTORY_CONTINUITY_INCLUDE_BLOCKED_GROUP_B is deprecated; use HISTORY_CONTINUITY_INCLUDE_DETAIL_FACTS=1"
      fi
    fi
    run_step receipt_core_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_receipt_core_replay_adapter.py"
    run_step receipt_header_pending run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_core_write.py"
    if [[ -f "$ROOT_DIR/migration_assets/20_business/receipt/receipt_core_v1.xml" ]]; then
      echo "[history.continuity] skip legacy receipt recovery lanes because receipt_core_v1.xml replay is authoritative"
    else
      run_step receipt_partner_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_receipt_partner_targeted_replay_adapter.py"
      run_step receipt_partner_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_receipt_partner_targeted_replay_write.py"
      run_step receipt_parent_recovery_adapter python3 "$ROOT_DIR/scripts/migration/history_receipt_parent_recovery_adapter.py"
      run_step receipt_parent_recovery_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_receipt_parent_recovery_write.py"
    fi
    run_step receipt_invoice_line_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_receipt_invoice_line_replay_adapter.py"
    run_step receipt_core_creator_visible_surface_normalize run_odoo_script "$ROOT_DIR/scripts/migration/visible_surface_receipt_core_creator_normalize_write.py"
    run_step receipt_request_scope_normalize run_odoo_script "$ROOT_DIR/scripts/migration/visible_surface_receipt_request_scope_normalize_write.py"
    run_step receipt_invoice_line_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_invoice_line_replay_write.py"
    run_step receipt_invoice_line_visible_surface_normalize run_odoo_script "$ROOT_DIR/scripts/migration/visible_surface_receipt_invoice_line_normalize_write.py"
    run_step receipt_invoice_attachment_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_receipt_invoice_attachment_replay_adapter.py"
    run_step receipt_invoice_attachment_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_invoice_attachment_replay_write.py"
    run_step outflow_request_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_outflow_request_replay_adapter.py"
    run_step outflow_partner_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_outflow_partner_targeted_replay_adapter.py"
    run_step outflow_partner_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_outflow_partner_targeted_replay_write.py"
    run_step outflow_request_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_outflow_request_replay_write.py"
    run_step outflow_request_fact_coverage run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_outflow_request_fact_coverage_write.py"
    run_step actual_outflow_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_actual_outflow_replay_adapter.py"
    run_step actual_outflow_partner_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_actual_outflow_partner_targeted_replay_adapter.py"
    run_step actual_outflow_partner_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_actual_outflow_partner_targeted_replay_write.py"
    run_step actual_outflow_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_actual_outflow_replay_write.py"
    if [[ "$INCLUDE_DETAIL_FACTS" == "1" ]]; then
      run_step outflow_request_line_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_outflow_request_line_replay_adapter.py"
      run_step outflow_request_line_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_outflow_request_line_replay_write.py"
      run_step actual_outflow_residual_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_actual_outflow_residual_replay_adapter.py"
      run_step actual_outflow_residual_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_actual_outflow_residual_replay_write.py"
      run_step actual_outflow_line_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_actual_outflow_line_replay_adapter.py"
      run_step actual_outflow_line_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_actual_outflow_line_replay_write.py"
    else
      echo "[history.continuity] skip payment request line facts by HISTORY_CONTINUITY_INCLUDE_DETAIL_FACTS=0"
    fi
    run_step payment_request_contract_visible_surface_normalize run_odoo_script "$ROOT_DIR/scripts/migration/visible_surface_payment_request_contract_normalize_write.py"
    run_step legacy_attachment_backfill_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_attachment_backfill_replay_adapter.py"
    run_step project_member_attachment_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_project_member_attachment_targeted_replay_adapter.py"
    run_step project_member_attachment_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_project_member_attachment_targeted_replay_write.py"
    run_step legacy_attachment_backfill_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_attachment_backfill_replay_write.py"
    run_step legacy_receipt_income_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_receipt_income_replay_adapter.py"
    run_step receipt_income_partner_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_receipt_income_partner_targeted_replay_adapter.py"
    run_step receipt_income_partner_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_receipt_income_partner_targeted_replay_write.py"
    run_step legacy_receipt_income_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_receipt_income_replay_write.py"
    run_step legacy_self_funding_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_self_funding_replay_adapter.py"
    run_step legacy_self_funding_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_self_funding_replay_write.py"
    run_step legacy_project_fund_balance_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_project_fund_balance_replay_adapter.py"
    run_step legacy_project_fund_balance_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_project_fund_balance_replay_write.py"
    run_step legacy_invoice_surcharge_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_surcharge_replay_adapter.py"
    run_step legacy_invoice_surcharge_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_surcharge_replay_write.py"
    run_step legacy_supplier_contract_pricing_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_supplier_contract_pricing_replay_adapter.py"
    run_step legacy_supplier_contract_pricing_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_supplier_contract_pricing_replay_write.py"
    run_step legacy_expense_deposit_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_expense_deposit_replay_adapter.py"
    run_step expense_deposit_partner_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_expense_deposit_partner_targeted_replay_adapter.py"
    run_step expense_deposit_partner_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_expense_deposit_partner_targeted_replay_write.py"
    run_step legacy_expense_deposit_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_expense_deposit_replay_write.py"
    run_step legacy_income_invoice_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_income_invoice_replay_adapter.py"
    run_step legacy_income_invoice_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_income_invoice_replay_write.py"
    run_step legacy_invoice_tax_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_tax_replay_adapter.py"
    run_step legacy_invoice_tax_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_tax_replay_write.py"
    run_step legacy_tax_deduction_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_tax_deduction_replay_adapter.py"
    run_step legacy_tax_deduction_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_tax_deduction_replay_write.py"
    run_step legacy_invoice_registration_line_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_registration_line_replay_adapter.py"
    run_step legacy_invoice_registration_line_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_registration_line_replay_write.py"
    run_step legacy_deduction_adjustment_line_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_deduction_adjustment_line_replay_adapter.py"
    run_step legacy_deduction_adjustment_line_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_deduction_adjustment_line_replay_write.py"
    run_step legacy_fund_confirmation_line_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_confirmation_line_replay_adapter.py"
    run_step legacy_fund_confirmation_line_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_confirmation_line_replay_write.py"
    run_step legacy_expense_reimbursement_line_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_expense_reimbursement_line_replay_adapter.py"
    run_step legacy_expense_reimbursement_line_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_expense_reimbursement_line_replay_write.py"
    run_step legacy_construction_diary_line_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_construction_diary_line_replay_adapter.py"
    run_step legacy_construction_diary_line_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_construction_diary_line_replay_write.py"
    run_step legacy_payment_residual_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_payment_residual_replay_adapter.py"
    run_step legacy_payment_residual_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_payment_residual_replay_write.py"
    run_step legacy_receipt_residual_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_receipt_residual_replay_adapter.py"
    run_step legacy_receipt_residual_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_receipt_residual_replay_write.py"
    run_step legacy_workflow_audit_adapter run_legacy_workflow_audit_adapter
    run_step legacy_workflow_audit_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_workflow_audit_replay_write.py"
    if [[ "$INCLUDE_FORMAL_PROJECTIONS" == "1" ]]; then
      run_step history_todo_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_history_todo_projection_write.py"
      run_step project_task_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_project_task_projection_write.py"
      run_step treasury_ledger_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_treasury_ledger_projection_write.py"
    else
      echo "[history.continuity] skip formal projections by HISTORY_CONTINUITY_INCLUDE_FORMAL_PROJECTIONS=0"
    fi
    if [[ "$INCLUDE_PAYMENT_STATE_RECOVERY" == "1" ]]; then
      run_step payment_request_outflow_state_activation_adapter run_payment_request_outflow_state_activation_adapter
      run_step payment_request_outflow_state_activation_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_payment_request_outflow_state_activation_write.py"
      run_step payment_request_outflow_approved_recovery_adapter python3 "$ROOT_DIR/scripts/migration/history_payment_request_outflow_approved_recovery_adapter.py"
      run_step payment_request_outflow_approved_recovery_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_payment_request_outflow_approved_recovery_write.py"
      run_step payment_request_outflow_done_recovery_adapter python3 "$ROOT_DIR/scripts/migration/history_payment_request_outflow_done_recovery_adapter.py"
      run_step payment_request_outflow_done_recovery_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_payment_request_outflow_done_recovery_write.py"
    else
      echo "[history.continuity] skip payment outflow state recovery by HISTORY_CONTINUITY_INCLUDE_PAYMENT_STATE_RECOVERY=0"
    fi
    if [[ "$INCLUDE_PROJECT_LIFECYCLE_CONTINUITY" == "1" ]]; then
      run_step project_lifecycle_continuity_adapter python3 "$ROOT_DIR/scripts/migration/history_project_lifecycle_continuity_adapter.py"
      run_step project_lifecycle_continuity_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_project_lifecycle_continuity_write.py"
    else
      echo "[history.continuity] skip project lifecycle continuity by HISTORY_CONTINUITY_INCLUDE_PROJECT_LIFECYCLE_CONTINUITY=0"
    fi
    run_step legacy_financing_loan_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_financing_loan_replay_adapter.py"
    run_step legacy_financing_loan_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_financing_loan_replay_write.py"
    run_step legacy_fund_daily_snapshot_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_daily_snapshot_replay_adapter.py"
    run_step legacy_fund_daily_snapshot_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_daily_snapshot_replay_write.py"
    run_step legacy_fund_daily_line_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_daily_line_replay_adapter.py"
    run_step legacy_fund_daily_line_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_daily_line_replay_write.py"
    if [[ "$INCLUDE_FORMAL_PROJECTIONS" == "1" ]]; then
      run_step settlement_adjustment_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_settlement_adjustment_projection_write.py"
      run_step expense_claim_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_expense_claim_projection_write.py"
      run_step deposit_claim_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_deposit_claim_projection_write.py"
      run_step deposit_claim_taxonomy_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_deposit_claim_taxonomy_projection_write.py"
      run_step repayment_registration_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_repayment_registration_projection_write.py"
      run_step contractor_project_repay_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contractor_project_repay_projection_write.py"
      run_step project_repay_company_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_project_repay_company_projection_write.py"
      run_step deduction_bill_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_deduction_bill_projection_write.py"
      run_step deduction_paid_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_deduction_paid_projection_write.py"
      run_step deduction_paid_refund_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_deduction_paid_refund_projection_write.py"
      run_step treasury_reconciliation_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_treasury_reconciliation_projection_write.py"
      run_step receipt_income_missing_project_anchor run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_income_missing_project_anchor_write.py"
      run_step receipt_income_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_income_projection_write.py"
      run_step receipt_income_from_payment_request_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_income_from_payment_request_projection_write.py"
      run_step receipt_income_type_normalize run_odoo_script "$ROOT_DIR/scripts/migration/visible_surface_receipt_income_type_normalize_write.py"
      run_step arrival_confirmation_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_arrival_confirmation_projection_write.py"
      run_step payment_execution_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_payment_execution_projection_write.py"
      run_step payment_execution_taxonomy_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_payment_execution_taxonomy_projection_write.py"
      run_step actual_outflow_line_payment_execution_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_actual_outflow_line_payment_execution_projection_write.py"
      run_step invoice_contract_anchor_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_invoice_contract_anchor_projection_write.py"
      run_step invoice_registration_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_invoice_registration_projection_write.py"
      run_step financing_loan_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_financing_loan_projection_write.py"
      run_step construction_contract_income_count_alignment run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_construction_contract_income_count_alignment_write.py"
      run_step new_construction_contract_xlsx_income run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_new_construction_contract_xlsx_income_write.py"
      run_step income_fact_project_stub run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_income_fact_project_stub_write.py"
      run_step project_contract_visible_surface_enrichment run_odoo_script "$ROOT_DIR/scripts/migration/visible_surface_project_contract_enrichment_write.py"
      run_step project_migration_field_continuity_backfill run_odoo_write_script "$ROOT_DIR/scripts/migration/project_migration_field_continuity_backfill_write.py"
      run_step general_contract_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_general_contract_projection_write.py"
      run_step construction_diary_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_construction_diary_projection_write.py"
      run_step fund_account_between_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_fund_account_between_projection_write.py"
      run_step fund_daily_report_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_fund_daily_report_projection_write.py"
      run_step tender_registration_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_tender_registration_projection_write.py"
      run_step material_stock_document_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_material_stock_document_projection_write.py"
      run_step project_budget_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_project_budget_projection_write.py"
      run_step labor_equipment_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_labor_equipment_projection_write.py"
      run_step work_breakdown_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_work_breakdown_projection_write.py"
      run_step office_admin_leave_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_office_admin_leave_projection_write.py"
      run_step office_admin_seal_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_office_admin_seal_projection_write.py"
      run_step hr_payroll_salary_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_hr_payroll_salary_projection_write.py"
      run_step hr_payroll_social_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_hr_payroll_social_projection_write.py"
      run_step hr_payroll_allowance_bonus_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_hr_payroll_allowance_bonus_projection_write.py"
      run_step document_certificate_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_document_certificate_projection_write.py"
      run_step document_borrow_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_document_borrow_projection_write.py"
      run_step document_admin_archive_projection run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_document_admin_archive_projection_write.py"
    else
      echo "[history.continuity] skip runtime formal projections by HISTORY_CONTINUITY_INCLUDE_FORMAL_PROJECTIONS=0"
    fi
    if [[ "$INCLUDE_FORMAL_PROJECTIONS" == "1" ]]; then
      run_step attachment_custody_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_attachment_custody_probe.py"
      run_step invoice_tax_runtime_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_invoice_tax_runtime_probe.py"
      run_step settlement_adjustment_runtime_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_settlement_adjustment_runtime_probe.py"
      run_step expense_claim_runtime_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_expense_claim_runtime_probe.py"
      run_step treasury_reconciliation_runtime_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_treasury_reconciliation_runtime_probe.py"
      run_step receipt_income_runtime_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_receipt_income_runtime_probe.py"
      run_step payment_execution_runtime_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_payment_execution_runtime_probe.py"
      run_step financing_loan_runtime_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_financing_loan_runtime_probe.py"
      run_step general_contract_runtime_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_general_contract_runtime_probe.py"
      run_step construction_diary_runtime_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_construction_diary_runtime_probe.py"
      run_step treasury_reconciliation_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_treasury_reconciliation_probe.py"
      run_step expense_deposit_runtime_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_expense_deposit_runtime_probe.py"
      run_step material_catalog_runtime_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_material_catalog_runtime_probe.py"
      run_step purchase_contract_runtime_probe run_odoo_script "$ROOT_DIR/scripts/migration/history_purchase_contract_runtime_probe.py"
      run_step usability_probe run_odoo_script "$PROBE_SCRIPT"
    else
      echo "[history.continuity] skip projection-dependent runtime probes by HISTORY_CONTINUITY_INCLUDE_FORMAL_PROJECTIONS=0"
    fi
    ;;
  *)
    echo "❌ unsupported HISTORY_CONTINUITY_MODE: $MODE" >&2
    exit 2
    ;;
esac

echo "[history.continuity] done mode=$MODE db=$DB_NAME artifact_root=$ARTIFACT_ROOT"
