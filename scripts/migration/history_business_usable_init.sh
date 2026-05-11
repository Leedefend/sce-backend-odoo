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
run_odoo_script workbench_item_projection "$ROOT_DIR/scripts/migration/fresh_db_workbench_item_projection_write.py"
run_odoo_script organization_department_materialize "$ROOT_DIR/scripts/migration/history_organization_department_materialize_write.py"
run_odoo_script supplier_contract_pricing_projection "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_pricing_projection_write.py"
run_odoo_script dashboard_cockpit_projection "$ROOT_DIR/scripts/migration/fresh_db_dashboard_cockpit_projection_write.py"
run_odoo_script treasury_ledger_projection "$ROOT_DIR/scripts/migration/fresh_db_treasury_ledger_projection_write.py"
run_odoo_script settlement_adjustment_projection "$ROOT_DIR/scripts/migration/fresh_db_settlement_adjustment_projection_write.py"
run_odoo_script expense_claim_projection "$ROOT_DIR/scripts/migration/fresh_db_expense_claim_projection_write.py"
run_odoo_script treasury_reconciliation_projection "$ROOT_DIR/scripts/migration/fresh_db_treasury_reconciliation_projection_write.py"
run_odoo_script receipt_income_projection "$ROOT_DIR/scripts/migration/fresh_db_receipt_income_projection_write.py"
run_odoo_script payment_execution_projection "$ROOT_DIR/scripts/migration/fresh_db_payment_execution_projection_write.py"
run_odoo_script invoice_registration_projection "$ROOT_DIR/scripts/migration/fresh_db_invoice_registration_projection_write.py"
run_odoo_script financing_loan_projection "$ROOT_DIR/scripts/migration/fresh_db_financing_loan_projection_write.py"
run_odoo_script general_contract_projection "$ROOT_DIR/scripts/migration/fresh_db_general_contract_projection_write.py"
run_odoo_script partner_semantic_normalize "$ROOT_DIR/scripts/migration/prod_sim_partner_semantic_normalize_write.py"
run_odoo_script construction_diary_projection "$ROOT_DIR/scripts/migration/fresh_db_construction_diary_projection_write.py"
run_odoo_script material_category_projection "$ROOT_DIR/scripts/migration/fresh_db_material_category_projection_write.py"
run_odoo_script material_catalog_projection "$ROOT_DIR/scripts/migration/fresh_db_material_catalog_projection_write.py"
run_odoo_script business_user_priority_menu_plan "$ROOT_DIR/scripts/migration/business_user_priority_menu_plan_write.py"
run_odoo_script formal_projection_refresh_probe "$ROOT_DIR/scripts/verify/formal_projection_refresh_probe.py"
run_odoo_script business_usable_probe "$ROOT_DIR/scripts/migration/history_business_usable_probe.py"

echo "[history.business.usable.init] PASS db=${DB_NAME} artifact_root=${ARTIFACT_ROOT}"
