#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${1:?usage: scbs_no_legacy_replay_apply.sh DB_NAME [ASSET_ROOT] [RUN_ARTIFACT_ROOT]}"
ASSET_ROOT="${2:-/mnt/artifacts/migration/scbs_replay_asset_v1}"
RUN_ARTIFACT_ROOT="${3:-/tmp/scbs_no_legacy_replay_${DB_NAME}}"
CONTAINER="${SCBS_ODOO_CONTAINER:-sc-backend-odoo-prod-sim-odoo-1}"
ODOO_CONF="${SCBS_ODOO_CONF:-/var/lib/odoo/odoo.conf}"

run_shell() {
  local label="$1"
  local script="$2"
  shift 2
  echo "### ${label}"
  docker exec -i \
    -e MIGRATION_REPLAY_DB_ALLOWLIST="${DB_NAME}" \
    -e MIGRATION_REPO_ROOT="${ASSET_ROOT}" \
    -e MIGRATION_ARTIFACT_ROOT="${RUN_ARTIFACT_ROOT}" \
    "$@" \
    "${CONTAINER}" odoo shell -d "${DB_NAME}" -c "${ODOO_CONF}" < "${script}"
}

echo "### reset_run_artifacts"
docker exec -i -u 0 "${CONTAINER}" sh -lc "rm -rf '${RUN_ARTIFACT_ROOT}' && mkdir -p '${RUN_ARTIFACT_ROOT}' && chown -R odoo:odoo '${RUN_ARTIFACT_ROOT}'"

run_shell business_entity_candidate scripts/migration/scbs_business_entity_candidate_import.py -e SCBS_BUSINESS_ENTITY_IMPORT_MODE=write
run_shell project_candidate scripts/migration/scbs_project_candidate_import.py -e SCBS_PROJECT_CANDIDATE_IMPORT_MODE=write
run_shell partner_duplicate_candidate scripts/migration/scbs_partner_candidate_import.py -e SCBS_PARTNER_CANDIDATE_IMPORT_MODE=write
run_shell fact_staging_import_initial scripts/migration/scbs_fact_staging_import.py -e SCBS_FACT_STAGING_IMPORT_MODE=write
run_shell dimension_backfill scripts/migration/scbs_fact_dimension_backfill_import.py -e SCBS_FACT_DIMENSION_BACKFILL_MODE=write
run_shell business_entity_bootstrap scripts/migration/scbs_business_entity_bootstrap.py -e SCBS_BUSINESS_ENTITY_BOOTSTRAP_APPLY=1
run_shell project_fact_bootstrap scripts/migration/scbs_project_fact_bootstrap.py -e SCBS_PROJECT_FACT_BOOTSTRAP_APPLY=1
run_shell partner_fact_candidate_import scripts/migration/scbs_partner_fact_candidate_import.py -e SCBS_PARTNER_FACT_CANDIDATE_IMPORT_MODE=write
run_shell fact_staging_bind_partner_maps scripts/migration/scbs_fact_staging_import.py -e SCBS_FACT_STAGING_IMPORT_MODE=write
run_shell partner_fact_bootstrap scripts/migration/scbs_partner_fact_bootstrap.py -e SCBS_PARTNER_FACT_BOOTSTRAP_APPLY=1
run_shell fact_staging_bind_targets scripts/migration/scbs_fact_staging_import.py -e SCBS_FACT_STAGING_IMPORT_MODE=write
run_shell base_system_project_links scripts/migration/scbs_base_system_project_link_import.py -e APPLY=1
run_shell operation_strategy_policy scripts/migration/scbs_operation_strategy_policy_refresh.py -e APPLY=1
run_shell project_operation_strategy_backfill scripts/migration/scbs_project_operation_strategy_backfill.py -e APPLY=1
run_shell material_map_import scripts/migration/scbs_stock_in_material_map_import.py -e SCBS_MATERIAL_MAPPING_CSV="${ASSET_ROOT}/artifacts/migration/scbs_stock_in_material_mapping_workbook_v1.csv"
run_shell material_catalog_bootstrap scripts/migration/scbs_material_catalog_bootstrap.py -e SCBS_MATERIAL_BOOTSTRAP_APPLY=1 -e SCBS_MATERIAL_BOOTSTRAP_LINK_EXACT=1 -e SCBS_MATERIAL_BOOTSTRAP_CREATE_MISSING=1
run_shell material_conflict_accept scripts/migration/scbs_material_conflict_catalog_accept.py -e APPLY=1
run_shell payment_contract_projection scripts/migration/scbs_payment_contract_projection.py -e APPLY=1
run_shell negative_payment_adjustment_projection scripts/migration/scbs_negative_payment_adjustment_projection.py -e APPLY=1
run_shell enterprise_no_project_fact_projection scripts/migration/scbs_enterprise_no_project_fact_projection.py -e APPLY=1
run_shell stock_in_projection scripts/migration/scbs_stock_in_projection.py -e APPLY=1 -e SCBS_STOCK_IN_LINE_CSV="${ASSET_ROOT}/artifacts/migration/scbs_stock_in_legacy_lines_v1.csv"
run_shell fund_daily_enterprise_projection scripts/migration/scbs_fund_daily_enterprise_projection.py -e APPLY=1 -e SCBS_FUND_DAILY_SOURCE_CSV="${ASSET_ROOT}/artifacts/migration/scbs_fund_daily_source_v1.csv"
run_shell residual_exclusion_final scripts/migration/scbs_residual_fact_exclusion.py -e SCBS_RESIDUAL_FACT_EXCLUSION_APPLY=1
run_shell closure_reconciliation scripts/migration/scbs_migration_closure_reconciliation.py
run_shell no_legacy_replay_acceptance scripts/migration/scbs_no_legacy_replay_acceptance.py
run_shell release_acceptance_strict scripts/migration/scbs_release_acceptance.py -e SCBS_ACCEPTANCE_MODE=strict
