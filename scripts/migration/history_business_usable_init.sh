#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

: "${DB_NAME:?DB_NAME is required}"

ARTIFACT_ROOT="${FORMAL_PROJECTION_ARTIFACT_ROOT:-${MIGRATION_ARTIFACT_ROOT:-/tmp/history_continuity/${DB_NAME}/business_usable_init}}"
ALLOWLIST="${MIGRATION_REPLAY_DB_ALLOWLIST:-$DB_NAME}"

export MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT"
export MIGRATION_REPLAY_DB_ALLOWLIST="$ALLOWLIST"

run_odoo_script() {
  local label="$1"
  local script_path="$2"
  echo "[history.business.usable.init] step=${label}"
  DB_NAME="$DB_NAME" \
    COMPOSE_FILES="${COMPOSE_FILES:-}" \
    MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT" \
    MIGRATION_REPLAY_DB_ALLOWLIST="$ALLOWLIST" \
    bash "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" <"$script_path"
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
run_odoo_script project_contract_visible_surface_enrichment "$ROOT_DIR/scripts/migration/visible_surface_project_contract_enrichment_write.py"
run_odoo_script dashboard_cockpit_projection "$ROOT_DIR/scripts/migration/fresh_db_dashboard_cockpit_projection_write.py"
run_odoo_script payment_request_contract_visible_surface_normalize "$ROOT_DIR/scripts/migration/visible_surface_payment_request_contract_normalize_write.py"
run_odoo_script treasury_ledger_projection "$ROOT_DIR/scripts/migration/fresh_db_treasury_ledger_projection_write.py"
run_odoo_script receipt_core_creator_visible_surface_normalize "$ROOT_DIR/scripts/migration/visible_surface_receipt_core_creator_normalize_write.py"
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
run_odoo_script receipt_income_projection "$ROOT_DIR/scripts/migration/fresh_db_receipt_income_projection_write.py"
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
run_odoo_script formal_projection_refresh_probe "$ROOT_DIR/scripts/verify/formal_projection_refresh_probe.py"
run_odoo_script formal_business_backfill_audit_probe "$ROOT_DIR/scripts/verify/formal_business_backfill_audit_probe.py"
run_odoo_script business_usable_probe "$ROOT_DIR/scripts/migration/history_business_usable_probe.py"

echo "[history.business.usable.init] PASS db=${DB_NAME} artifact_root=${ARTIFACT_ROOT}"
