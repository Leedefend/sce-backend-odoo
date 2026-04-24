#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"

: "${DB_NAME:?DB_NAME is required}"

guard_prod_forbid

MODE="${HISTORY_CONTINUITY_MODE:-rehearse}"
RUN_ID="${RUN_ID:-$(date +%Y%m%dT%H%M%S)}"
ALLOWED_DBS="${MIGRATION_REPLAY_DB_ALLOWLIST:-sc_migration_fresh,sc_demo}"
ARTIFACT_ROOT="${MIGRATION_ARTIFACT_ROOT:-/tmp/history_continuity/${DB_NAME}/${RUN_ID}}"
START_AT="${HISTORY_CONTINUITY_START_AT:-}"
export MIGRATION_REPO_ROOT="${MIGRATION_REPO_ROOT:-$ROOT_DIR}"
export MIGRATION_REPLAY_DB_ALLOWLIST="$ALLOWED_DBS"
export MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT"

SHELL_EXEC="$ROOT_DIR/scripts/ops/odoo_shell_exec.sh"
PRECHECK_SCRIPT="$ROOT_DIR/scripts/migration/fresh_db_replay_payload_precheck.py"
PROBE_SCRIPT="$ROOT_DIR/scripts/migration/history_continuity_usability_probe.py"
USER_REBUILD="$ROOT_DIR/scripts/migration/user_history_rebuild.sh"
CONTRACT_COUNTERPARTY_ADAPTER="$ROOT_DIR/scripts/migration/fresh_db_contract_counterparty_partner_replay_adapter.py"
RECEIPT_COUNTERPARTY_ADAPTER="$ROOT_DIR/scripts/migration/fresh_db_receipt_counterparty_partner_replay_adapter.py"
CONTRACT_LINE_ADAPTER="$ROOT_DIR/scripts/migration/fresh_db_contract_line_replay_adapter.py"
SUPPLIER_CONTRACT_ADAPTER="$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_replay_adapter.py"
SUPPLIER_CONTRACT_LINE_ADAPTER="$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_line_replay_adapter.py"
INCLUDE_BLOCKED_GROUP_B="${HISTORY_CONTINUITY_INCLUDE_BLOCKED_GROUP_B:-0}"

run_odoo_script() {
  local script_path="$1"
  DB_NAME="$DB_NAME" \
  MIGRATION_REPO_ROOT="$MIGRATION_REPO_ROOT" \
  MIGRATION_REPLAY_DB_ALLOWLIST="$MIGRATION_REPLAY_DB_ALLOWLIST" \
  MIGRATION_ARTIFACT_ROOT="$MIGRATION_ARTIFACT_ROOT" \
  bash "$SHELL_EXEC" <"$script_path"
}

run_python_validator() {
  local script_path="$1"
  MIGRATION_REPO_ROOT="$MIGRATION_REPO_ROOT" \
  MIGRATION_ARTIFACT_ROOT="$MIGRATION_ARTIFACT_ROOT" \
  python3 "$script_path"
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
  "$@"
}

echo "[history.continuity] mode=$MODE db=$DB_NAME artifact_root=$ARTIFACT_ROOT"

case "$MODE" in
  rehearse)
    run_step manifest_dry_run run_python_validator "$ROOT_DIR/scripts/migration/fresh_db_replay_runner_dry_run.py"
    run_step user_asset_verify python3 "$ROOT_DIR/scripts/migration/user_asset_verify.py" --asset-root "$ROOT_DIR/migration_assets" --lane user --check
    run_step replay_payload_precheck run_odoo_script "$PRECHECK_SCRIPT"
    run_step usability_probe run_odoo_script "$PROBE_SCRIPT"
    ;;
  replay)
    run_step user_rebuild bash -c "DB_NAME=\"$DB_NAME\" MIGRATION_REPO_ROOT=\"$MIGRATION_REPO_ROOT\" MIGRATION_ARTIFACT_ROOT=\"$MIGRATION_ARTIFACT_ROOT\" bash \"$USER_REBUILD\""
    run_step replay_payload_precheck run_odoo_script "$PRECHECK_SCRIPT"
    run_step partner_l4_anchor_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_partner_l4_replay_write.py"
    run_step project_anchor_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_project_anchor_replay_write.py"
    run_step contract_counterparty_partner_adapter python3 "$CONTRACT_COUNTERPARTY_ADAPTER"
    run_step contract_counterparty_partner_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_counterparty_partner_replay_write.py"
    run_step receipt_counterparty_partner_adapter python3 "$RECEIPT_COUNTERPARTY_ADAPTER"
    run_step receipt_counterparty_partner_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_counterparty_partner_replay_write.py"
    run_step project_member_neutral_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_project_member_neutral_replay_write.py"
    run_step contract_header_completed_1332 run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_remaining_write.py"
    run_step contract_missing_partner_anchors run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_missing_partner_anchor_write.py"
    run_step contract_12_missing_partner_anchors run_odoo_script "$ROOT_DIR/scripts/migration/contract_12_row_missing_partner_anchor_write.py"
    run_step contract_header_special_12 run_odoo_script "$ROOT_DIR/scripts/migration/contract_12_row_create_only_write.py"
    run_step contract_header_retry_57 run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_57_retry_write.py"
    run_step contract_unreached_ready_adapter python3 "$ROOT_DIR/scripts/migration/history_contract_unreached_ready_replay_adapter.py"
    run_step contract_unreached_ready_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_contract_unreached_ready_replay_write.py"
    run_step partner_master_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_partner_master_targeted_replay_adapter.py"
    run_step partner_master_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_partner_master_targeted_replay_write.py"
    run_step contract_partner_recovery_adapter python3 "$ROOT_DIR/scripts/migration/history_contract_partner_recovery_adapter.py"
    run_step contract_partner_recovery_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_contract_partner_recovery_write.py"
    run_step partner_master_direction_defer_adapter python3 "$ROOT_DIR/scripts/migration/history_partner_master_direction_defer_replay_adapter.py"
    run_step partner_master_direction_defer_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_partner_master_direction_defer_replay_write.py"
    run_step contract_direction_defer_recovery_adapter python3 "$ROOT_DIR/scripts/migration/history_contract_direction_defer_recovery_adapter.py"
    run_step contract_direction_defer_recovery_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_contract_direction_defer_recovery_write.py"
    if [[ "$INCLUDE_BLOCKED_GROUP_B" == "1" ]]; then
      run_step contract_line_adapter python3 "$CONTRACT_LINE_ADAPTER"
      run_step contract_line_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_line_replay_write.py"
      run_step supplier_contract_adapter python3 "$SUPPLIER_CONTRACT_ADAPTER"
      run_step supplier_contract_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_replay_write.py"
      run_step supplier_contract_line_adapter python3 "$SUPPLIER_CONTRACT_LINE_ADAPTER"
      run_step supplier_contract_line_completed run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_line_replay_write.py"
    else
      echo "[history.continuity] skip blocked Group B lanes by default"
    fi
    run_step receipt_header_pending run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_core_write.py"
    run_step receipt_partner_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_receipt_partner_targeted_replay_adapter.py"
    run_step receipt_partner_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_receipt_partner_targeted_replay_write.py"
    run_step receipt_parent_recovery_adapter python3 "$ROOT_DIR/scripts/migration/history_receipt_parent_recovery_adapter.py"
    run_step receipt_parent_recovery_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_receipt_parent_recovery_write.py"
    run_step receipt_invoice_line_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_receipt_invoice_line_replay_adapter.py"
    run_step receipt_invoice_line_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_invoice_line_replay_write.py"
    run_step receipt_invoice_attachment_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_receipt_invoice_attachment_replay_adapter.py"
    run_step receipt_invoice_attachment_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_invoice_attachment_replay_write.py"
    run_step project_member_attachment_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_project_member_attachment_targeted_replay_adapter.py"
    run_step project_member_attachment_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_project_member_attachment_targeted_replay_write.py"
    run_step legacy_attachment_backfill_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_attachment_backfill_replay_adapter.py"
    run_step legacy_attachment_backfill_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_attachment_backfill_replay_write.py"
    run_step receipt_income_partner_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_receipt_income_partner_targeted_replay_adapter.py"
    run_step receipt_income_partner_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_receipt_income_partner_targeted_replay_write.py"
    run_step legacy_receipt_income_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_receipt_income_replay_adapter.py"
    run_step legacy_receipt_income_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_receipt_income_replay_write.py"
    run_step expense_deposit_partner_targeted_adapter python3 "$ROOT_DIR/scripts/migration/history_expense_deposit_partner_targeted_replay_adapter.py"
    run_step expense_deposit_partner_targeted_replay run_odoo_script "$ROOT_DIR/scripts/migration/history_expense_deposit_partner_targeted_replay_write.py"
    run_step legacy_expense_deposit_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_expense_deposit_replay_adapter.py"
    run_step legacy_expense_deposit_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_expense_deposit_replay_write.py"
    run_step legacy_invoice_tax_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_tax_replay_adapter.py"
    run_step legacy_invoice_tax_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_tax_replay_write.py"
    run_step legacy_workflow_audit_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_workflow_audit_replay_adapter.py"
    run_step legacy_workflow_audit_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_workflow_audit_replay_write.py"
    run_step legacy_financing_loan_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_financing_loan_replay_adapter.py"
    run_step legacy_financing_loan_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_financing_loan_replay_write.py"
    run_step legacy_fund_daily_snapshot_adapter python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_daily_snapshot_replay_adapter.py"
    run_step legacy_fund_daily_snapshot_replay run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_daily_snapshot_replay_write.py"
    run_step usability_probe run_odoo_script "$PROBE_SCRIPT"
    ;;
  *)
    echo "❌ unsupported HISTORY_CONTINUITY_MODE: $MODE" >&2
    exit 2
    ;;
esac

echo "[history.continuity] done mode=$MODE db=$DB_NAME artifact_root=$ARTIFACT_ROOT"
