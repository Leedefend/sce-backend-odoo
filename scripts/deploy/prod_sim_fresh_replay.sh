#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../_lib/common.sh
source "$ROOT_DIR/scripts/_lib/common.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"

: "${DB_NAME:?DB_NAME is required}"

guard_prod_forbid

CONFIRM_VALUE="${PROD_SIM_FRESH_REPLAY:-}"
if [[ "$CONFIRM_VALUE" != "1" ]]; then
  echo "❌ prod-sim fresh replay is destructive for the isolated prod-sim volumes." >&2
  echo "   Re-run with PROD_SIM_FRESH_REPLAY=1 after confirming DB_NAME=${DB_NAME}." >&2
  exit 2
fi

COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.prod-sim.yml}"
RUN_ID="${RUN_ID:-prod_sim_fresh_replay_$(date +%Y%m%dT%H%M%S)}"
ARTIFACT_ROOT="${MIGRATION_ARTIFACT_ROOT:-$ROOT_DIR/artifacts/migration/${RUN_ID}}"
CONTAINER_ARTIFACT_ROOT="${MIGRATION_CONTAINER_ARTIFACT_ROOT:-/mnt/artifacts/migration/${RUN_ID}}"
DATA_REPLAY_ASSET_ROOT="${DATA_REPLAY_ASSET_ROOT:-$ROOT_DIR}"
SCBS_REPLAY_ASSET_ROOT="${SCBS_REPLAY_ASSET_ROOT:-/mnt/artifacts/migration/scbs_replay_asset_v1}"
PRODUCTION_MODULES="${HISTORY_PRODUCTION_MODULES:-smart_construction_bootstrap,smart_core,smart_scene,smart_construction_core,smart_construction_portal,smart_construction_scene,smart_license_core,smart_owner_core,smart_owner_bundle,smart_construction_bundle,smart_construction_seed}"

export COMPOSE_FILES
export RUN_ID
export MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT"
export MIGRATION_REPLAY_DB_ALLOWLIST="${MIGRATION_REPLAY_DB_ALLOWLIST:-$DB_NAME}"
export PROD_DANGER=1
export HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS="${HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS:-1}"
export HISTORY_CONTINUITY_INCLUDE_PAYMENT_STATE_RECOVERY="${HISTORY_CONTINUITY_INCLUDE_PAYMENT_STATE_RECOVERY:-1}"
export HISTORY_CONTINUITY_INCLUDE_MATERIAL_CATALOG=0
export HISTORY_CONTINUITY_INCLUDE_FILE_INDEX="${HISTORY_CONTINUITY_INCLUDE_FILE_INDEX:-1}"
export BASE_URL="${BASE_URL:-http://127.0.0.1:18069}"

log "prod-sim fresh replay: db=${DB_NAME} run_id=${RUN_ID}"
log "prod-sim fresh replay: artifact_root=${MIGRATION_ARTIFACT_ROOT}"
log "prod-sim fresh replay: data_asset_root=${DATA_REPLAY_ASSET_ROOT}"
log "prod-sim fresh replay: scbs_asset_root=${SCBS_REPLAY_ASSET_ROOT}"
log "prod-sim fresh replay: compose_files=${COMPOSE_FILES}"

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "❌ missing required command: $cmd" >&2
    exit 2
  fi
}

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "❌ missing required file: $path" >&2
    exit 2
  fi
}

require_dir() {
  local path="$1"
  if [[ ! -d "$path" ]]; then
    echo "❌ missing required directory: $path" >&2
    exit 2
  fi
}

resolve_host_path() {
  local path="$1"
  case "$path" in
    /*)
      printf '%s\n' "$path"
      ;;
    *)
      printf '%s/%s\n' "$ROOT_DIR" "$path"
      ;;
  esac
}

install_asset_tree() {
  local source_dir="$1"
  local target_dir="$2"
  local label="$3"
  require_dir "$source_dir"
  mkdir -p "$target_dir"
  if [[ "$(realpath "$source_dir")" == "$(realpath "$target_dir")" ]]; then
    log "portable_preflight: ${label} assets already in target: ${target_dir}"
    return 0
  fi
  if [[ "${DATA_REPLAY_ASSET_OVERWRITE:-0}" == "1" ]]; then
    log "portable_preflight: install ${label} assets with overwrite: ${source_dir} -> ${target_dir}"
    cp -R "$source_dir"/. "$target_dir"/
  else
    log "portable_preflight: install missing ${label} assets: ${source_dir} -> ${target_dir}"
    cp -R -n "$source_dir"/. "$target_dir"/
  fi
}

DATA_REPLAY_ASSET_HOST_ROOT="$(resolve_host_path "$DATA_REPLAY_ASSET_ROOT")"
if [[ "$DATA_REPLAY_ASSET_HOST_ROOT" != "$ROOT_DIR" ]]; then
  require_dir "$DATA_REPLAY_ASSET_HOST_ROOT"
  if [[ -d "$DATA_REPLAY_ASSET_HOST_ROOT/artifacts/migration" ]]; then
    install_asset_tree "$DATA_REPLAY_ASSET_HOST_ROOT/artifacts/migration" "$ROOT_DIR/artifacts/migration" "history+scbs"
  elif [[ -d "$DATA_REPLAY_ASSET_HOST_ROOT/migration" ]]; then
    install_asset_tree "$DATA_REPLAY_ASSET_HOST_ROOT/migration" "$ROOT_DIR/artifacts/migration" "history+scbs"
  else
    echo "❌ data asset package must contain artifacts/migration or migration: $DATA_REPLAY_ASSET_HOST_ROOT" >&2
    exit 2
  fi
  if [[ -d "$DATA_REPLAY_ASSET_HOST_ROOT/migration_assets" ]]; then
    install_asset_tree "$DATA_REPLAY_ASSET_HOST_ROOT/migration_assets" "$ROOT_DIR/migration_assets" "migration_assets"
  else
    echo "❌ data asset package must contain migration_assets: $DATA_REPLAY_ASSET_HOST_ROOT" >&2
    exit 2
  fi
fi

host_scbs_asset_root="${SCBS_REPLAY_ASSET_ROOT#/mnt/}"
if [[ "$host_scbs_asset_root" == "$SCBS_REPLAY_ASSET_ROOT" ]]; then
  echo "❌ SCBS_REPLAY_ASSET_ROOT must be under /mnt so the Odoo container can read it: $SCBS_REPLAY_ASSET_ROOT" >&2
  exit 2
fi
host_scbs_asset_root="$ROOT_DIR/$host_scbs_asset_root"

log "step=portable_preflight"
require_command docker
if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
  echo "❌ docker compose or docker-compose is required" >&2
  exit 2
fi
require_file "$ROOT_DIR/docker-compose.yml"
require_file "$ROOT_DIR/docker-compose.prod-sim.yml"
require_file "$ROOT_DIR/Dockerfile"
require_file "$ROOT_DIR/scripts/migration/history_continuity_oneclick.sh"
require_file "$ROOT_DIR/scripts/migration/scbs_no_legacy_replay_apply.sh"
require_file "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh"
require_file "$ROOT_DIR/scripts/ops/ensure_core_tax_baseline.py"
require_dir "$ROOT_DIR/addons"
require_dir "$ROOT_DIR/artifacts/migration"
require_dir "$ROOT_DIR/migration_assets"
require_file "$ROOT_DIR/artifacts/migration/fresh_db_replay_manifest_v1.json"
require_file "$ROOT_DIR/migration_assets/manifest/migration_asset_catalog_v1.json"
history_payloads=(
  fresh_db_legacy_department_replay_payload_v1.csv
  fresh_db_legacy_user_profile_replay_payload_v1.csv
  fresh_db_legacy_user_role_replay_payload_v1.csv
  fresh_db_legacy_user_project_scope_replay_payload_v1.csv
  fresh_db_legacy_task_evidence_replay_payload_v1.csv
  fresh_db_partner_l4_replay_payload_v1.csv
  fresh_db_project_anchor_replay_payload_v1.csv
  fresh_db_legacy_account_master_replay_payload_v1.csv
  fresh_db_legacy_account_transaction_replay_payload_v1.csv
  fresh_db_legacy_file_index_replay_payload_v1.csv
  fresh_db_contract_counterparty_partner_replay_payload_v1.csv
  fresh_db_receipt_counterparty_partner_replay_payload_v1.csv
  fresh_db_project_member_neutral_replay_payload_v1.csv
  fresh_db_contract_remaining_replay_payload_v1.csv
  fresh_db_legacy_purchase_contract_replay_payload_v1.csv
  fresh_db_contract_line_replay_payload_v1.csv
  fresh_db_supplier_contract_replay_payload_v1.csv
  fresh_db_supplier_contract_line_replay_payload_v1.csv
  fresh_db_receipt_write_design_payload_v1.csv
  fresh_db_receipt_invoice_line_replay_payload_v1.csv
  fresh_db_receipt_invoice_attachment_replay_payload_v1.csv
  fresh_db_outflow_request_replay_payload_v1.csv
  fresh_db_actual_outflow_replay_payload_v1.csv
  fresh_db_outflow_request_line_replay_payload_v1.csv
  fresh_db_actual_outflow_residual_replay_payload_v1.csv
  fresh_db_actual_outflow_line_replay_payload_v1.csv
  fresh_db_legacy_attachment_backfill_replay_payload_v1.csv
  fresh_db_legacy_receipt_income_replay_payload_v1.csv
  fresh_db_legacy_self_funding_replay_payload_v1.csv
  fresh_db_legacy_project_fund_balance_replay_payload_v1.csv
  fresh_db_legacy_invoice_surcharge_replay_payload_v1.csv
  fresh_db_legacy_supplier_contract_pricing_replay_payload_v1.csv
  fresh_db_legacy_expense_deposit_replay_payload_v1.csv
  fresh_db_legacy_invoice_tax_replay_payload_v1.csv
  fresh_db_legacy_tax_deduction_replay_payload_v1.csv
  fresh_db_legacy_invoice_registration_line_replay_payload_v1.csv
  fresh_db_legacy_deduction_adjustment_line_replay_payload_v1.csv
  fresh_db_legacy_fund_confirmation_line_replay_payload_v1.csv
  fresh_db_legacy_expense_reimbursement_line_replay_payload_v1.csv
  fresh_db_legacy_construction_diary_line_replay_payload_v1.csv
  fresh_db_legacy_payment_residual_replay_payload_v1.csv
  fresh_db_legacy_receipt_residual_replay_payload_v1.csv
  fresh_db_legacy_workflow_audit_replay_payload_v1.csv
  fresh_db_legacy_financing_loan_replay_payload_v1.csv
  fresh_db_legacy_fund_daily_snapshot_replay_payload_v1.csv
  fresh_db_legacy_fund_daily_line_replay_payload_v1.csv
  history_outflow_partner_targeted_replay_payload_v1.csv
  history_actual_outflow_partner_targeted_replay_payload_v1.csv
  history_project_member_attachment_targeted_replay_payload_v1.csv
  history_receipt_income_partner_targeted_replay_payload_v1.csv
  history_expense_deposit_partner_targeted_replay_payload_v1.csv
  history_supplier_partner_targeted_replay_payload_v1.csv
)
for payload in "${history_payloads[@]}"; do
  require_file "$ROOT_DIR/artifacts/migration/$payload"
done
if [[ "$HISTORY_CONTINUITY_INCLUDE_PAYMENT_STATE_RECOVERY" == "1" ]]; then
  require_file "$ROOT_DIR/artifacts/migration/history_payment_request_outflow_state_activation_payload_v1.csv"
  require_file "$ROOT_DIR/artifacts/migration/history_payment_request_outflow_approved_recovery_payload_v1.csv"
  require_file "$ROOT_DIR/artifacts/migration/history_payment_request_outflow_done_recovery_payload_v1.csv"
fi
require_dir "$host_scbs_asset_root"
require_file "$host_scbs_asset_root/manifest.json"
require_file "$host_scbs_asset_root/artifacts/migration/scbs_fact_staging_v1.csv"
require_file "$host_scbs_asset_root/artifacts/migration/scbs_stock_in_legacy_lines_v1.csv"
require_file "$host_scbs_asset_root/artifacts/migration/scbs_stock_in_material_mapping_workbook_v1.csv"
require_file "$host_scbs_asset_root/artifacts/migration/scbs_replay_expected_baseline_v1.json"

log "step=compose_config"
compose ${COMPOSE_FILES} config >/dev/null

if [[ "${PROD_SIM_FRESH_REPLAY_PREFLIGHT_ONLY:-0}" == "1" ]]; then
  log "prod-sim fresh replay portable preflight PASS"
  printf 'RUN_ID=%s\n' "$RUN_ID"
  printf 'MIGRATION_ARTIFACT_ROOT=%s\n' "$MIGRATION_ARTIFACT_ROOT"
  exit 0
fi

log "step=destroy_isolated_prod_sim_stack_and_volumes"
compose ${COMPOSE_FILES} down -v --remove-orphans

log "step=build_and_start_empty_stack"
compose ${COMPOSE_FILES} up -d --build

log "step=install_production_modules"
compose ${COMPOSE_FILES} exec -T odoo odoo \
  -d "$DB_NAME" \
  -c /var/lib/odoo/odoo.conf \
  -i "$PRODUCTION_MODULES" \
  --load-language="${SC_RUNTIME_LANG:-zh_CN}" \
  --without-demo=all \
  --stop-after-init

log "step=apply_extension_modules"
DB_NAME="$DB_NAME" COMPOSE_FILES="$COMPOSE_FILES" "$ROOT_DIR/scripts/ops/apply_extension_modules.sh"

log "step=prepare_migration_artifact_root"
compose ${COMPOSE_FILES} exec -T -u 0 odoo sh -lc \
  "mkdir -p '${CONTAINER_ARTIFACT_ROOT}' && chown -R odoo:odoo '${CONTAINER_ARTIFACT_ROOT}'"

log "step=ensure_core_tax_baseline"
DB_NAME="$DB_NAME" COMPOSE_FILES="$COMPOSE_FILES" \
  "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" <"$ROOT_DIR/scripts/ops/ensure_core_tax_baseline.py"

log "phase=1 step=history_continuity_data_replay"
DB_NAME="$DB_NAME" COMPOSE_FILES="$COMPOSE_FILES" \
  MIGRATION_REPO_ROOT="$ROOT_DIR" \
  MIGRATION_REPO_ROOT_ODOO="/mnt" \
  MIGRATION_ARTIFACT_ROOT="$ARTIFACT_ROOT" \
  MIGRATION_ARTIFACT_ROOT_ODOO="$CONTAINER_ARTIFACT_ROOT" \
  MIGRATION_REPLAY_DB_ALLOWLIST="$DB_NAME" \
  HISTORY_CONTINUITY_MODE=replay \
  HISTORY_CONTINUITY_INCLUDE_FORMAL_PROJECTIONS=0 \
  HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS="$HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS" \
  HISTORY_CONTINUITY_INCLUDE_MATERIAL_CATALOG=0 \
  HISTORY_CONTINUITY_INCLUDE_PAYMENT_STATE_RECOVERY="$HISTORY_CONTINUITY_INCLUDE_PAYMENT_STATE_RECOVERY" \
  HISTORY_CONTINUITY_INCLUDE_FILE_INDEX="$HISTORY_CONTINUITY_INCLUDE_FILE_INDEX" \
  REAL_USER_INITIAL_PASSWORD="${REAL_USER_INITIAL_PASSWORD:-123456}" \
  bash "$ROOT_DIR/scripts/migration/history_continuity_oneclick.sh"

log "step=ensure_runtime_language_baseline"
DB_NAME="$DB_NAME" COMPOSE_FILES="$COMPOSE_FILES" SC_RUNTIME_LANG="${SC_RUNTIME_LANG:-zh_CN}" \
  "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" <"$ROOT_DIR/scripts/ops/ensure_runtime_language_baseline.py"

log "step=restart_odoo"
compose ${COMPOSE_FILES} restart odoo

log "step=platform_init_preflight"
DB_NAME="$DB_NAME" COMPOSE_FILES="${COMPOSE_FILES}" "$ROOT_DIR/scripts/verify/platform_init_preflight.sh"

log "phase=1 step=scbs_no_legacy_business_replay"
SCBS_ODOO_CONTAINER="${SCBS_ODOO_CONTAINER:-${COMPOSE_PROJECT_NAME}-odoo-1}" \
  bash "$ROOT_DIR/scripts/migration/scbs_no_legacy_replay_apply.sh" \
  "$DB_NAME" \
  "$SCBS_REPLAY_ASSET_ROOT" \
  "$CONTAINER_ARTIFACT_ROOT"

log "phase=2 step=business_usable_init"
DB_NAME="$DB_NAME" COMPOSE_FILES="$COMPOSE_FILES" \
  MIGRATION_REPLAY_DB_ALLOWLIST="$DB_NAME" \
  FORMAL_PROJECTION_ARTIFACT_ROOT="$CONTAINER_ARTIFACT_ROOT" \
  MIGRATION_ARTIFACT_ROOT="$CONTAINER_ARTIFACT_ROOT" \
  bash "$ROOT_DIR/scripts/migration/history_business_usable_init.sh"

log "step=business_smoke"
DB_NAME="$DB_NAME" BASE_URL="$BASE_URL" "$ROOT_DIR/scripts/audit/smoke_business_full.sh"

log "step=role_matrix_smoke"
DB_NAME="$DB_NAME" BASE_URL="$BASE_URL" "$ROOT_DIR/scripts/audit/smoke_role_matrix.sh"

log "prod-sim fresh replay PASS"
printf 'RUN_ID=%s\n' "$RUN_ID"
printf 'MIGRATION_ARTIFACT_ROOT=%s\n' "$MIGRATION_ARTIFACT_ROOT"
