#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

: "${DB_NAME:?DB_NAME is required}"

ARTIFACT_ROOT="${FORMAL_PROJECTION_ARTIFACT_ROOT:-${MIGRATION_ARTIFACT_ROOT:-/tmp/history_continuity/${DB_NAME}/business_usable_init}}"
ALLOWLIST="${MIGRATION_REPLAY_DB_ALLOWLIST:-$DB_NAME}"
START_AT="${HISTORY_BUSINESS_USABLE_START_AT:-}"
STOP_AFTER="${HISTORY_BUSINESS_USABLE_STOP_AFTER:-}"
STARTED=0
if [[ -z "$START_AT" ]]; then
  STARTED=1
fi

export MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT"
export MIGRATION_REPLAY_DB_ALLOWLIST="$ALLOWLIST"

should_run_step() {
  local label="$1"
  if [[ "$STARTED" == "0" && "$label" != "$START_AT" ]]; then
    echo "[history.business.usable.init] skip step=${label} start_at=${START_AT}"
    return 1
  fi
  STARTED=1
  return 0
}

after_step() {
  local label="$1"
  if [[ -n "$STOP_AFTER" && "$label" == "$STOP_AFTER" ]]; then
    echo "[history.business.usable.init] stop_after=${STOP_AFTER}"
    exit 0
  fi
}

run_odoo_script() {
  local label="$1"
  local script_path="$2"
  should_run_step "$label" || return 0
  echo "[history.business.usable.init] step=${label}"
  DB_NAME="$DB_NAME" \
    COMPOSE_FILES="${COMPOSE_FILES:-}" \
    MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT" \
    MIGRATION_REPLAY_DB_ALLOWLIST="$ALLOWLIST" \
    bash "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" <"$script_path"
  after_step "$label"
}

run_odoo_write_script() {
  local label="$1"
  local script_path="$2"
  should_run_step "$label" || return 0
  echo "[history.business.usable.init] step=${label}"
  DB_NAME="$DB_NAME" \
    COMPOSE_FILES="${COMPOSE_FILES:-}" \
    MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT" \
    MIGRATION_REPLAY_DB_ALLOWLIST="$ALLOWLIST" \
    MIGRATION_WRITE_MODE=write \
    bash "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" <"$script_path"
  after_step "$label"
}

run_partner_role_alignment() {
  local label="partner_business_fact_role_alignment"
  local script_path="$ROOT_DIR/scripts/migration/partner_business_fact_role_alignment_write.py"
  should_run_step "$label" || return 0
  echo "[history.business.usable.init] step=${label}"
  DB_NAME="$DB_NAME" \
    COMPOSE_FILES="${COMPOSE_FILES:-}" \
    MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT" \
    MIGRATION_REPLAY_DB_ALLOWLIST="$ALLOWLIST" \
    MIGRATION_WRITE_MODE=write \
    PARTNER_FACT_ALIGNMENT_DEMOTE_NO_FACT=1 \
    bash "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" <"$script_path"
  after_step "$label"
}

echo "[history.business.usable.init] db=${DB_NAME} artifact_root=${ARTIFACT_ROOT}"

run_odoo_script real_user_normalize "$ROOT_DIR/scripts/migration/history_real_user_normalize_write.py"
run_odoo_script wutao_business_config_probe "$ROOT_DIR/scripts/migration/history_wutao_business_config_probe.py"
run_odoo_script fund_account_projection "$ROOT_DIR/scripts/migration/fresh_db_fund_account_projection_write.py"
run_odoo_script history_todo_projection "$ROOT_DIR/scripts/migration/fresh_db_history_todo_projection_write.py"
run_odoo_script project_task_projection "$ROOT_DIR/scripts/migration/fresh_db_project_task_projection_write.py"
run_odoo_script workbench_item_projection "$ROOT_DIR/scripts/migration/fresh_db_workbench_item_projection_write.py"
run_odoo_script organization_department_materialize "$ROOT_DIR/scripts/migration/history_organization_department_materialize_write.py"
run_odoo_script supplier_contract_pricing_projection "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_pricing_projection_write.py"
run_odoo_script construction_contract_income_count_alignment "$ROOT_DIR/scripts/migration/fresh_db_construction_contract_income_count_alignment_write.py"
run_odoo_script new_construction_contract_xlsx_income "$ROOT_DIR/scripts/migration/fresh_db_new_construction_contract_xlsx_income_write.py"
run_odoo_script income_fact_project_stub "$ROOT_DIR/scripts/migration/fresh_db_income_fact_project_stub_write.py"
run_odoo_script construction_contract_history_value_gap_probe "$ROOT_DIR/scripts/verify/construction_contract_history_value_gap_probe.py"
run_odoo_script project_contract_visible_surface_enrichment "$ROOT_DIR/scripts/migration/visible_surface_project_contract_enrichment_write.py"
run_odoo_write_script project_migration_field_continuity_backfill "$ROOT_DIR/scripts/migration/project_migration_field_continuity_backfill_write.py"
run_odoo_script project_migration_field_continuity_gap_probe "$ROOT_DIR/scripts/verify/project_migration_field_continuity_gap_probe.py"
run_odoo_script dashboard_cockpit_projection "$ROOT_DIR/scripts/migration/fresh_db_dashboard_cockpit_projection_write.py"
run_odoo_script payment_request_contract_visible_surface_normalize "$ROOT_DIR/scripts/migration/visible_surface_payment_request_contract_normalize_write.py"
run_odoo_script payment_request_amount_uppercase_recompute "$ROOT_DIR/scripts/migration/payment_request_amount_uppercase_recompute_write.py"
run_odoo_script treasury_ledger_projection "$ROOT_DIR/scripts/migration/fresh_db_treasury_ledger_projection_write.py"
run_odoo_script receipt_core_creator_visible_surface_normalize "$ROOT_DIR/scripts/migration/visible_surface_receipt_core_creator_normalize_write.py"
run_odoo_script receipt_request_scope_normalize "$ROOT_DIR/scripts/migration/visible_surface_receipt_request_scope_normalize_write.py"
run_odoo_script settlement_adjustment_projection "$ROOT_DIR/scripts/migration/fresh_db_settlement_adjustment_projection_write.py"
run_odoo_script expense_claim_projection "$ROOT_DIR/scripts/migration/fresh_db_expense_claim_projection_write.py"
run_odoo_script deposit_claim_projection "$ROOT_DIR/scripts/migration/fresh_db_deposit_claim_projection_write.py"
run_odoo_script deposit_claim_taxonomy_projection "$ROOT_DIR/scripts/migration/fresh_db_deposit_claim_taxonomy_projection_write.py"
run_odoo_script repayment_registration_projection "$ROOT_DIR/scripts/migration/fresh_db_repayment_registration_projection_write.py"
run_odoo_script contractor_project_repay_projection "$ROOT_DIR/scripts/migration/fresh_db_contractor_project_repay_projection_write.py"
run_odoo_script project_repay_company_projection "$ROOT_DIR/scripts/migration/fresh_db_project_repay_company_projection_write.py"
run_odoo_script deduction_bill_projection "$ROOT_DIR/scripts/migration/fresh_db_deduction_bill_projection_write.py"
run_odoo_script deduction_paid_projection "$ROOT_DIR/scripts/migration/fresh_db_deduction_paid_projection_write.py"
run_odoo_script deduction_paid_refund_projection "$ROOT_DIR/scripts/migration/fresh_db_deduction_paid_refund_projection_write.py"
run_odoo_script treasury_reconciliation_projection "$ROOT_DIR/scripts/migration/fresh_db_treasury_reconciliation_projection_write.py"
run_odoo_script receipt_income_missing_project_anchor "$ROOT_DIR/scripts/migration/fresh_db_receipt_income_missing_project_anchor_write.py"
run_odoo_script receipt_income_projection "$ROOT_DIR/scripts/migration/fresh_db_receipt_income_projection_write.py"
run_odoo_script receipt_income_from_payment_request_projection "$ROOT_DIR/scripts/migration/fresh_db_receipt_income_from_payment_request_projection_write.py"
run_odoo_script receipt_income_type_normalize "$ROOT_DIR/scripts/migration/visible_surface_receipt_income_type_normalize_write.py"
run_odoo_script arrival_confirmation_projection "$ROOT_DIR/scripts/migration/fresh_db_arrival_confirmation_projection_write.py"
run_odoo_script payment_execution_projection "$ROOT_DIR/scripts/migration/fresh_db_payment_execution_projection_write.py"
run_odoo_script payment_execution_taxonomy_projection "$ROOT_DIR/scripts/migration/fresh_db_payment_execution_taxonomy_projection_write.py"
run_odoo_script actual_outflow_line_payment_execution_projection "$ROOT_DIR/scripts/migration/fresh_db_actual_outflow_line_payment_execution_projection_write.py"
run_odoo_script invoice_contract_anchor_projection "$ROOT_DIR/scripts/migration/fresh_db_invoice_contract_anchor_projection_write.py"
run_odoo_script invoice_registration_projection "$ROOT_DIR/scripts/migration/fresh_db_invoice_registration_projection_write.py"
run_odoo_script tax_deduction_registration_projection "$ROOT_DIR/scripts/migration/fresh_db_tax_deduction_registration_projection_write.py"
run_odoo_script financing_loan_projection "$ROOT_DIR/scripts/migration/fresh_db_financing_loan_projection_write.py"
run_odoo_script general_contract_projection "$ROOT_DIR/scripts/migration/fresh_db_general_contract_projection_write.py"
run_odoo_script partner_semantic_normalize "$ROOT_DIR/scripts/migration/prod_sim_partner_semantic_normalize_write.py"
run_odoo_script construction_diary_projection "$ROOT_DIR/scripts/migration/fresh_db_construction_diary_projection_write.py"
run_odoo_script fund_account_between_projection "$ROOT_DIR/scripts/migration/fresh_db_fund_account_between_projection_write.py"
run_odoo_script fund_daily_report_projection "$ROOT_DIR/scripts/migration/fresh_db_fund_daily_report_projection_write.py"
run_odoo_script tender_registration_projection "$ROOT_DIR/scripts/migration/fresh_db_tender_registration_projection_write.py"
run_odoo_script material_category_projection "$ROOT_DIR/scripts/migration/fresh_db_material_category_projection_write.py"
run_odoo_script material_catalog_projection "$ROOT_DIR/scripts/migration/fresh_db_material_catalog_projection_write.py"
run_odoo_script material_stock_document_projection "$ROOT_DIR/scripts/migration/fresh_db_material_stock_document_projection_write.py"
run_odoo_script project_budget_projection "$ROOT_DIR/scripts/migration/fresh_db_project_budget_projection_write.py"
run_odoo_script project_cost_ledger_projection "$ROOT_DIR/scripts/migration/project_cost_ledger_projection_write.py"
run_odoo_script labor_equipment_projection "$ROOT_DIR/scripts/migration/fresh_db_labor_equipment_projection_write.py"
run_odoo_script work_breakdown_projection "$ROOT_DIR/scripts/migration/fresh_db_work_breakdown_projection_write.py"
run_odoo_script office_admin_leave_projection "$ROOT_DIR/scripts/migration/fresh_db_office_admin_leave_projection_write.py"
run_odoo_script office_admin_seal_projection "$ROOT_DIR/scripts/migration/fresh_db_office_admin_seal_projection_write.py"
run_odoo_script hr_payroll_salary_projection "$ROOT_DIR/scripts/migration/fresh_db_hr_payroll_salary_projection_write.py"
run_odoo_script hr_payroll_social_projection "$ROOT_DIR/scripts/migration/fresh_db_hr_payroll_social_projection_write.py"
run_odoo_script hr_payroll_allowance_bonus_projection "$ROOT_DIR/scripts/migration/fresh_db_hr_payroll_allowance_bonus_projection_write.py"
run_odoo_script document_certificate_projection "$ROOT_DIR/scripts/migration/fresh_db_document_certificate_projection_write.py"
run_odoo_script document_borrow_projection "$ROOT_DIR/scripts/migration/fresh_db_document_borrow_projection_write.py"
run_odoo_script document_admin_archive_projection "$ROOT_DIR/scripts/migration/fresh_db_document_admin_archive_projection_write.py"
run_odoo_script business_user_priority_menu_plan "$ROOT_DIR/scripts/migration/business_user_priority_menu_plan_write.py"
run_odoo_write_script legacy_business_menu_exposure_close "$ROOT_DIR/scripts/migration/history_legacy_business_menu_exposure_close_write.py"
run_partner_role_alignment
run_odoo_script formal_entry_metadata_surface "$ROOT_DIR/scripts/ops/formal_entry_metadata_surface_write.py"
run_odoo_script project_cost_ledger_projection_refresh "$ROOT_DIR/scripts/migration/project_cost_ledger_projection_write.py"
run_odoo_script formal_projection_refresh_probe "$ROOT_DIR/scripts/verify/formal_projection_refresh_probe.py"
run_odoo_script formal_business_backfill_audit_probe "$ROOT_DIR/scripts/verify/formal_business_backfill_audit_probe.py"
run_odoo_script business_usable_probe "$ROOT_DIR/scripts/migration/history_business_usable_probe.py"

echo "[history.business.usable.init] PASS db=${DB_NAME} artifact_root=${ARTIFACT_ROOT}"
