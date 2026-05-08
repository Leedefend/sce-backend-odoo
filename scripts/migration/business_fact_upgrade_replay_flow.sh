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
ACCEPTANCE_SUMMARY_SCRIPT="$ROOT_DIR/scripts/migration/business_fact_acceptance_bundle_summary.py"

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
    BUSINESS_FACT_EXPECTED_PROJECT_ROWS="${BUSINESS_FACT_EXPECTED_PROJECT_ROWS:-798}" \
    BUSINESS_FACT_EXPECTED_CONTRACT_TOTAL="${BUSINESS_FACT_EXPECTED_CONTRACT_TOTAL:-6850}" \
    BUSINESS_FACT_EXPECTED_INCOME_CONTRACTS="${BUSINESS_FACT_EXPECTED_INCOME_CONTRACTS:-1541}" \
    BUSINESS_FACT_EXPECTED_EXPENSE_CONTRACTS="${BUSINESS_FACT_EXPECTED_EXPENSE_CONTRACTS:-5309}" \
    BUSINESS_FACT_EXPECTED_CONTRACT_LINES="${BUSINESS_FACT_EXPECTED_CONTRACT_LINES:-6566}" \
    BUSINESS_FACT_EXPECTED_GENERAL_CONTRACTS="${BUSINESS_FACT_EXPECTED_GENERAL_CONTRACTS:-41}" \
    BUSINESS_FACT_EXPECTED_PURCHASE_FACTS="${BUSINESS_FACT_EXPECTED_PURCHASE_FACTS:-49}" \
    BUSINESS_FACT_EXPECTED_VISIBLE_INVOICE_FACTS="${BUSINESS_FACT_EXPECTED_VISIBLE_INVOICE_FACTS:-6}" \
    BUSINESS_FACT_EXPECTED_VISIBLE_RECEIPT_FACTS="${BUSINESS_FACT_EXPECTED_VISIBLE_RECEIPT_FACTS:-5}" \
    bash "$SHELL_EXEC" <"$script_path"
}

run_adapters() {
  echo "[business.fact.replay] step=adapters"
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
}

run_writes() {
  if [[ "${BUSINESS_FACT_REPLAY_EXECUTE_WRITES:-0}" != "1" ]]; then
    echo "❌ write mode requires BUSINESS_FACT_REPLAY_EXECUTE_WRITES=1" >&2
    exit 2
  fi
  echo "[business.fact.replay] step=writes db=$DB_NAME"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_counterparty_partner_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_remaining_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_contract_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_supplier_contract_line_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_legacy_purchase_contract_replay_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_construction_contract_visible_business_fact_write.py"
  run_odoo_script "$ROOT_DIR/scripts/migration/fresh_db_general_contract_projection_write.py"
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
    run_expense_fact_taxonomy_acceptance
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
    run_expense_fact_taxonomy_acceptance
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
    run_expense_fact_taxonomy_acceptance
    run_acceptance_summary
    ;;
  *)
    echo "❌ unsupported BUSINESS_FACT_REPLAY_MODE=$MODE (adapters|postcheck|cleanup|legacy-source|acceptance|write|all)" >&2
    exit 2
    ;;
esac

echo "[business.fact.replay] complete mode=$MODE artifact_root=$ARTIFACT_ROOT"
