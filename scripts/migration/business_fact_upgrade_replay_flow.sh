#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"

MODE="${BUSINESS_FACT_REPLAY_MODE:-postcheck}"
RUN_ID="${RUN_ID:-$(date +%Y%m%dT%H%M%S)}"
ARTIFACT_ROOT="${MIGRATION_ARTIFACT_ROOT:-$ROOT_DIR/artifacts/migration/business_fact_upgrade/$RUN_ID}"
ALLOWED_DBS="${MIGRATION_REPLAY_DB_ALLOWLIST:-sc_partner_acceptance,sc_migration_fresh,sc_demo}"
SHELL_EXEC="$ROOT_DIR/scripts/ops/odoo_shell_exec.sh"
POSTCHECK_SCRIPT="$ROOT_DIR/scripts/migration/fresh_db_business_fact_replay_postcheck.py"
BALANCE_CLEANUP_SCRIPT="$ROOT_DIR/scripts/migration/business_fact_visible_balance_cleanup.py"
LEGACY_SOURCE_PROBE_SCRIPT="$ROOT_DIR/scripts/migration/business_fact_visible_balance_legacy_source_probe.py"
ADDITIONAL_FACT_INVENTORY_SCRIPT="$ROOT_DIR/scripts/migration/business_fact_additional_fact_inventory.py"
EXPENSE_FACT_TAXONOMY_ACCEPTANCE_SCRIPT="$ROOT_DIR/scripts/migration/business_expense_fact_taxonomy_acceptance.py"
EXPENSE_CONTRACT_SUBTYPE_EVIDENCE_SCRIPT="$ROOT_DIR/scripts/migration/business_expense_contract_subtype_evidence.py"
EXPENSE_PAYMENT_FACT_ACCEPTANCE_SCRIPT="$ROOT_DIR/scripts/migration/business_expense_contract_payment_fact_acceptance.py"
ACCEPTANCE_SUMMARY_SCRIPT="$ROOT_DIR/scripts/migration/business_fact_acceptance_bundle_summary.py"
ATTACHMENT_CUSTODY_PROBE_SCRIPT="$ROOT_DIR/scripts/migration/history_attachment_custody_probe.py"
FULL_LEGACY_LOSS_SCAN_SCRIPT="$ROOT_DIR/scripts/migration/legacy_db_full_business_fact_loss_scan.py"
REMAINING_FACT_FAMILY_SCREEN_SCRIPT="$ROOT_DIR/scripts/migration/legacy_db_remaining_business_fact_family_screen.py"
MULTI_DB_FACT_SCAN_SUMMARY_SCRIPT="$ROOT_DIR/scripts/migration/legacy_multi_db_business_fact_scan_summary.py"

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

if [[ -z "${BUSINESS_FACT_REPLAY_COMPOSE_PROJECT_NAME:-}" && "${DB_NAME:-}" == "sc_partner_acceptance" ]]; then
  BUSINESS_FACT_REPLAY_COMPOSE_PROJECT_NAME="sc-backend-odoo-partner-acceptance"
fi
BUSINESS_FACT_REPLAY_COMPOSE_PROJECT_NAME="${BUSINESS_FACT_REPLAY_COMPOSE_PROJECT_NAME:-${COMPOSE_PROJECT_NAME:-}}"

if [[ "${BUSINESS_FACT_REPLAY_ALLOW_PROD:-0}" == "1" ]]; then
  guard_prod_danger
else
  guard_prod_forbid
fi

run_odoo_script() {
  local script_path="$1"
  DB_NAME="$DB_NAME" \
    COMPOSE_PROJECT_NAME="${BUSINESS_FACT_REPLAY_COMPOSE_PROJECT_NAME:-}" \
    PROJECT="${BUSINESS_FACT_REPLAY_COMPOSE_PROJECT_NAME:-}" \
    MIGRATION_REPO_ROOT="$MIGRATION_REPO_ROOT_ODOO" \
    MIGRATION_ARTIFACT_ROOT="$MIGRATION_ARTIFACT_ROOT_ODOO" \
    MIGRATION_REPLAY_DB_ALLOWLIST="$MIGRATION_REPLAY_DB_ALLOWLIST" \
    BUSINESS_FACT_EXPECTED_PROJECT_ROWS="${BUSINESS_FACT_EXPECTED_PROJECT_ROWS:-810}" \
    BUSINESS_FACT_EXPECTED_CONTRACT_TOTAL="${BUSINESS_FACT_EXPECTED_CONTRACT_TOTAL:-6985}" \
    BUSINESS_FACT_EXPECTED_INCOME_CONTRACTS="${BUSINESS_FACT_EXPECTED_INCOME_CONTRACTS:-1537}" \
    BUSINESS_FACT_EXPECTED_EXPENSE_CONTRACTS="${BUSINESS_FACT_EXPECTED_EXPENSE_CONTRACTS:-5448}" \
    BUSINESS_FACT_EXPECTED_CONTRACT_LINES="${BUSINESS_FACT_EXPECTED_CONTRACT_LINES:-6566}" \
    BUSINESS_FACT_EXPECTED_GENERAL_CONTRACTS="${BUSINESS_FACT_EXPECTED_GENERAL_CONTRACTS:-45}" \
    BUSINESS_FACT_EXPECTED_PURCHASE_FACTS="${BUSINESS_FACT_EXPECTED_PURCHASE_FACTS:-49}" \
    BUSINESS_FACT_EXPECTED_VISIBLE_INVOICE_FACTS="${BUSINESS_FACT_EXPECTED_VISIBLE_INVOICE_FACTS:-6}" \
    BUSINESS_FACT_EXPECTED_VISIBLE_RECEIPT_FACTS="${BUSINESS_FACT_EXPECTED_VISIBLE_RECEIPT_FACTS:-5}" \
    bash "$SHELL_EXEC" <"$script_path"
}

run_adapters() {
  echo "[business.fact.replay] step=adapters"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_user_context_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_user_project_scope_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_project_anchor_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_partner_l4_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_material_catalog_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_tender_registration_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_labor_subcontract_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_material_stock_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_equipment_lease_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_income_invoice_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_contract_counterparty_partner_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_contract_remaining_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_contract_line_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_line_replay_adapter.py"
  if [[ "${BUSINESS_FACT_REPLAY_REFRESH_LEGACY_PURCHASE:-0}" == "1" ]]; then
    python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_purchase_contract_replay_adapter.py"
  else
    echo "[business.fact.replay] skip legacy purchase contract adapter by BUSINESS_FACT_REPLAY_REFRESH_LEGACY_PURCHASE=0"
  fi
  python3 "$ROOT_DIR/scripts/migration/fresh_db_project_member_neutral_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_receipt_counterparty_partner_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/history_receipt_core_partner_targeted_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_receipt_core_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_receipt_income_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_receipt_residual_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_receipt_invoice_line_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_receipt_invoice_attachment_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_file_index_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/history_project_member_attachment_targeted_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_attachment_backfill_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_workflow_audit_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_workflow_detail_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_task_evidence_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_registration_line_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_surcharge_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_tax_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_tax_deduction_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_confirmation_line_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_daily_snapshot_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_daily_line_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_project_fund_balance_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_expense_deposit_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/history_expense_deposit_partner_targeted_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_expense_reimbursement_line_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_self_funding_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_financing_loan_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_account_master_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_account_transaction_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_finance_auxiliary_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_payment_residual_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_construction_diary_line_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_salary_line_replay_adapter.py"
  python3 "$ROOT_DIR/scripts/migration/fresh_db_legacy_attendance_checkin_replay_adapter.py"
}

run_writes() {
  if [[ "${BUSINESS_FACT_REPLAY_EXECUTE_WRITES:-0}" != "1" ]]; then
    echo "❌ write mode requires BUSINESS_FACT_REPLAY_EXECUTE_WRITES=1" >&2
    exit 2
  fi
  echo "[business.fact.replay] step=writes db=$DB_NAME"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_user_context_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_user_project_scope_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_project_anchor_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_partner_l4_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_material_catalog_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_tender_registration_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_labor_subcontract_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_material_stock_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_equipment_lease_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_income_invoice_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_counterparty_partner_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_remaining_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_supplier_contract_pricing_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_pricing_projection_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_purchase_contract_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_construction_contract_visible_business_fact_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_general_contract_projection_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/history_outflow_partner_targeted_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/history_actual_outflow_partner_targeted_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_outflow_request_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_actual_outflow_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_actual_outflow_residual_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_outflow_request_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_actual_outflow_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/history_payment_request_outflow_state_activation_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/history_payment_request_outflow_approved_recovery_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/history_payment_request_outflow_done_recovery_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_payment_residual_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_payment_execution_projection_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_actual_outflow_line_payment_execution_projection_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_deduction_adjustment_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_settlement_adjustment_projection_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_project_member_neutral_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_counterparty_partner_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/history_receipt_core_partner_targeted_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_core_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_receipt_income_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_receipt_residual_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_invoice_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_receipt_invoice_attachment_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_file_index_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/history_project_member_attachment_targeted_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_attachment_backfill_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_workflow_audit_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_workflow_detail_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_task_evidence_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_registration_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_surcharge_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_invoice_tax_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_tax_deduction_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_confirmation_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_daily_snapshot_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_fund_daily_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_project_fund_balance_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/history_expense_deposit_partner_targeted_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_expense_deposit_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_expense_reimbursement_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_self_funding_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_financing_loan_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_account_master_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_account_transaction_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_finance_auxiliary_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_construction_diary_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_salary_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_attendance_checkin_replay_write.py"
}

run_postcheck() {
  echo "[business.fact.replay] step=postcheck db=$DB_NAME"
  run_odoo_script "$POSTCHECK_SCRIPT"
}

run_cleanup() {
  echo "[business.fact.replay] step=cleanup db=$DB_NAME"
  run_odoo_script "$BALANCE_CLEANUP_SCRIPT"
}

run_legacy_source_probe() {
  if [[ "${BUSINESS_FACT_REPLAY_LEGACY_SOURCE_PROBE:-0}" != "1" ]]; then
    echo "[business.fact.replay] skip legacy-source by BUSINESS_FACT_REPLAY_LEGACY_SOURCE_PROBE=0"
    return 0
  fi
  echo "[business.fact.replay] step=legacy-source artifact_root=$ARTIFACT_ROOT"
  ROOT_DIR="$ROOT_DIR" MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT" python3 "$LEGACY_SOURCE_PROBE_SCRIPT"
}

run_additional_fact_inventory() {
  echo "[business.fact.replay] step=additional-fact-inventory artifact_root=$ARTIFACT_ROOT"
  ROOT_DIR="$ROOT_DIR" MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT" python3 "$ADDITIONAL_FACT_INVENTORY_SCRIPT"
}

run_expense_fact_taxonomy_acceptance() {
  echo "[business.fact.replay] step=expense-fact-taxonomy db=$DB_NAME"
  run_odoo_script "$EXPENSE_FACT_TAXONOMY_ACCEPTANCE_SCRIPT"
}

run_expense_payment_fact_acceptance() {
  echo "[business.fact.replay] step=expense-payment-facts db=$DB_NAME"
  run_odoo_script "$EXPENSE_PAYMENT_FACT_ACCEPTANCE_SCRIPT"
}

run_attachment_custody_probe() {
  echo "[business.fact.replay] step=attachment-custody db=$DB_NAME"
  run_odoo_script "$ATTACHMENT_CUSTODY_PROBE_SCRIPT"
}

legacy_source_artifact_root() {
  local label="$1"
  if [[ "$label" == "main" ]]; then
    printf '%s\n' "$ARTIFACT_ROOT"
  else
    printf '%s/%s\n' "$ARTIFACT_ROOT" "$label"
  fi
}

run_full_legacy_loss_scans() {
  local sources="${LEGACY_BUSINESS_FACT_SOURCES:-main:legacy-mssql-restore:LegacyDb,scbs:legacy-mssql-scbs:LegacyScbs20260417}"
  echo "[business.fact.replay] step=full-legacy-loss-scans artifact_root=$ARTIFACT_ROOT sources=$sources"
  IFS=',' read -r -a source_items <<<"$sources"
  for source_item in "${source_items[@]}"; do
    IFS=':' read -r label container database <<<"$source_item"
    if [[ -z "$label" || -z "$container" || -z "$database" ]]; then
      echo "❌ invalid LEGACY_BUSINESS_FACT_SOURCES item=$source_item expected label:container:database" >&2
      exit 2
    fi
    local source_artifact_root
    source_artifact_root="$(legacy_source_artifact_root "$label")"
    mkdir -p "$source_artifact_root"
    echo "[business.fact.replay] step=full-legacy-loss-scan source=$label container=$container database=$database artifact_root=$source_artifact_root"
    MIGRATION_ARTIFACT_ROOT="$source_artifact_root" LEGACY_MSSQL_CONTAINER="$container" LEGACY_MSSQL_DATABASE="$database" python3 "$FULL_LEGACY_LOSS_SCAN_SCRIPT"
  done
}

run_remaining_fact_family_screens() {
  local sources="${LEGACY_BUSINESS_FACT_SOURCES:-main:legacy-mssql-restore:LegacyDb,scbs:legacy-mssql-scbs:LegacyScbs20260417}"
  echo "[business.fact.replay] step=remaining-fact-family-screens artifact_root=$ARTIFACT_ROOT sources=$sources"
  IFS=',' read -r -a source_items <<<"$sources"
  for source_item in "${source_items[@]}"; do
    IFS=':' read -r label container database <<<"$source_item"
    if [[ -z "$label" || -z "$container" || -z "$database" ]]; then
      echo "❌ invalid LEGACY_BUSINESS_FACT_SOURCES item=$source_item expected label:container:database" >&2
      exit 2
    fi
    local source_artifact_root
    source_artifact_root="$(legacy_source_artifact_root "$label")"
    echo "[business.fact.replay] step=remaining-fact-family-screen source=$label container=$container database=$database artifact_root=$source_artifact_root"
    MIGRATION_ARTIFACT_ROOT="$source_artifact_root" LEGACY_MSSQL_CONTAINER="$container" LEGACY_MSSQL_DATABASE="$database" python3 "$REMAINING_FACT_FAMILY_SCREEN_SCRIPT"
  done
}

run_multi_db_fact_scan_summary() {
  local sources="${LEGACY_BUSINESS_FACT_SOURCES:-main:legacy-mssql-restore:LegacyDb,scbs:legacy-mssql-scbs:LegacyScbs20260417}"
  echo "[business.fact.replay] step=multi-db-fact-scan-summary artifact_root=$ARTIFACT_ROOT sources=$sources"
  MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT" LEGACY_BUSINESS_FACT_SOURCES="$sources" python3 "$MULTI_DB_FACT_SCAN_SUMMARY_SCRIPT"
}

run_expense_contract_subtype_evidence() {
  echo "[business.fact.replay] step=expense-contract-subtype-evidence artifact_root=$ARTIFACT_ROOT"
  ROOT_DIR="$ROOT_DIR" MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT" python3 "$EXPENSE_CONTRACT_SUBTYPE_EVIDENCE_SCRIPT"
}

run_acceptance_summary() {
  echo "[business.fact.replay] step=acceptance-summary artifact_root=$ARTIFACT_ROOT"
  MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT" python3 "$ACCEPTANCE_SUMMARY_SCRIPT"
}

case "$MODE" in
  adapters)
    mkdir -p "$ARTIFACT_ROOT"
    run_adapters
    ;;
  postcheck)
    : "${DB_NAME:?DB_NAME is required for BUSINESS_FACT_REPLAY_MODE=postcheck}"
    mkdir -p "$ARTIFACT_ROOT"
    chmod 0777 "$ARTIFACT_ROOT" 2>/dev/null || true
    echo "[business.fact.replay] mode=$MODE db=$DB_NAME artifact_root=$ARTIFACT_ROOT allowlist=$MIGRATION_REPLAY_DB_ALLOWLIST compose_project=${BUSINESS_FACT_REPLAY_COMPOSE_PROJECT_NAME:-default}"
    run_postcheck
    ;;
  cleanup)
    : "${DB_NAME:?DB_NAME is required for BUSINESS_FACT_REPLAY_MODE=cleanup}"
    mkdir -p "$ARTIFACT_ROOT"
    chmod 0777 "$ARTIFACT_ROOT" 2>/dev/null || true
    echo "[business.fact.replay] mode=$MODE db=$DB_NAME artifact_root=$ARTIFACT_ROOT allowlist=$MIGRATION_REPLAY_DB_ALLOWLIST compose_project=${BUSINESS_FACT_REPLAY_COMPOSE_PROJECT_NAME:-default}"
    run_cleanup
    ;;
  legacy-source)
    mkdir -p "$ARTIFACT_ROOT"
    chmod 0777 "$ARTIFACT_ROOT" 2>/dev/null || true
    echo "[business.fact.replay] mode=$MODE artifact_root=$ARTIFACT_ROOT legacy_container=${LEGACY_MSSQL_CONTAINER:-legacy-mssql-restore}"
    BUSINESS_FACT_REPLAY_LEGACY_SOURCE_PROBE=1 run_legacy_source_probe
    ;;
  acceptance)
    : "${DB_NAME:?DB_NAME is required for BUSINESS_FACT_REPLAY_MODE=acceptance}"
    mkdir -p "$ARTIFACT_ROOT"
    chmod 0777 "$ARTIFACT_ROOT" 2>/dev/null || true
    echo "[business.fact.replay] mode=$MODE db=$DB_NAME artifact_root=$ARTIFACT_ROOT allowlist=$MIGRATION_REPLAY_DB_ALLOWLIST compose_project=${BUSINESS_FACT_REPLAY_COMPOSE_PROJECT_NAME:-default}"
    run_postcheck
    run_cleanup
    run_legacy_source_probe
    run_additional_fact_inventory
    run_expense_contract_subtype_evidence
    run_expense_fact_taxonomy_acceptance
    run_expense_payment_fact_acceptance
    run_attachment_custody_probe
    run_full_legacy_loss_scans
    run_remaining_fact_family_screens
    run_multi_db_fact_scan_summary
    run_acceptance_summary
    ;;
  write)
    : "${DB_NAME:?DB_NAME is required for BUSINESS_FACT_REPLAY_MODE=write}"
    mkdir -p "$ARTIFACT_ROOT"
    chmod 0777 "$ARTIFACT_ROOT" 2>/dev/null || true
    echo "[business.fact.replay] mode=$MODE db=$DB_NAME artifact_root=$ARTIFACT_ROOT allowlist=$MIGRATION_REPLAY_DB_ALLOWLIST compose_project=${BUSINESS_FACT_REPLAY_COMPOSE_PROJECT_NAME:-default}"
    run_writes
    run_postcheck
    run_cleanup
    run_legacy_source_probe
    run_additional_fact_inventory
    run_expense_contract_subtype_evidence
    run_expense_fact_taxonomy_acceptance
    run_expense_payment_fact_acceptance
    run_attachment_custody_probe
    run_full_legacy_loss_scans
    run_remaining_fact_family_screens
    run_multi_db_fact_scan_summary
    run_acceptance_summary
    ;;
  all)
    : "${DB_NAME:?DB_NAME is required for BUSINESS_FACT_REPLAY_MODE=all}"
    mkdir -p "$ARTIFACT_ROOT"
    chmod 0777 "$ARTIFACT_ROOT" 2>/dev/null || true
    echo "[business.fact.replay] mode=$MODE db=$DB_NAME artifact_root=$ARTIFACT_ROOT allowlist=$MIGRATION_REPLAY_DB_ALLOWLIST compose_project=${BUSINESS_FACT_REPLAY_COMPOSE_PROJECT_NAME:-default}"
    run_adapters
    run_writes
    run_postcheck
    run_cleanup
    run_legacy_source_probe
    run_additional_fact_inventory
    run_expense_contract_subtype_evidence
    run_expense_fact_taxonomy_acceptance
    run_expense_payment_fact_acceptance
    run_attachment_custody_probe
    run_full_legacy_loss_scans
    run_remaining_fact_family_screens
    run_multi_db_fact_scan_summary
    run_acceptance_summary
    ;;
  *)
    echo "❌ unsupported BUSINESS_FACT_REPLAY_MODE=$MODE (adapters|postcheck|cleanup|legacy-source|acceptance|write|all)" >&2
    exit 2
    ;;
esac

echo "[business.fact.replay] complete mode=$MODE artifact_root=$ARTIFACT_ROOT"
