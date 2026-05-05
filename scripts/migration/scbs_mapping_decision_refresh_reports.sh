#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${SCBS_ODOO_CONTAINER:-sc-backend-odoo-prod-sim-odoo-1}"
DB="${SCBS_ODOO_DB:-sc_prod_sim}"
CONFIG="${SCBS_ODOO_CONFIG:-/var/lib/odoo/odoo.conf}"
HOST_ARTIFACT_DIR="${SCBS_HOST_ARTIFACT_DIR:-artifacts/migration}"
CONTAINER_ARTIFACT_DIR="${SCBS_CONTAINER_ARTIFACT_DIR:-/tmp}"

run_odoo_script() {
  local script="$1"
  docker exec -i \
    -e "MIGRATION_ARTIFACT_ROOT=${CONTAINER_ARTIFACT_DIR}" \
    "${CONTAINER}" \
    odoo shell -c "${CONFIG}" -d "${DB}" < "${script}"
}

copy_from_container() {
  local name="$1"
  docker cp "${CONTAINER}:${CONTAINER_ARTIFACT_DIR}/${name}" "${HOST_ARTIFACT_DIR}/${name}"
}

mkdir -p "${HOST_ARTIFACT_DIR}"

run_odoo_script scripts/migration/scbs_mapping_decision_workbook.py
copy_from_container scbs_mapping_decision_workbook_v1.csv
copy_from_container scbs_mapping_decision_workbook_result_v1.json
copy_from_container scbs_mapping_decision_action_summary_v1.csv
copy_from_container scbs_mapping_decision_priority_top_v1.csv

MIGRATION_ARTIFACT_ROOT="${HOST_ARTIFACT_DIR}" \
  python3 scripts/migration/scbs_mapping_decision_split_workbooks.py

run_odoo_script scripts/migration/scbs_partner_target_candidate_report.py
copy_from_container scbs_partner_target_candidate_report_v1.csv
copy_from_container scbs_partner_target_candidate_report_result_v1.json

run_odoo_script scripts/migration/scbs_project_target_candidate_report.py
copy_from_container scbs_project_target_candidate_report_v1.csv
copy_from_container scbs_project_target_candidate_report_result_v1.json

run_odoo_script scripts/migration/scbs_business_entity_consolidation_report.py
copy_from_container scbs_business_entity_consolidation_detail_v1.csv
copy_from_container scbs_business_entity_consolidation_summary_v1.csv
copy_from_container scbs_business_entity_consolidation_report_result_v1.json

run_odoo_script scripts/migration/scbs_mapping_decision_validate.py
copy_from_container scbs_mapping_decision_validate_result_v1.json
copy_from_container scbs_mapping_decision_validate_rows_v1.csv
copy_from_container scbs_mapping_decision_projection_simulation_v1.csv
copy_from_container scbs_mapping_decision_projection_blocked_examples_v1.csv

docker exec -i \
  -e "MIGRATION_ARTIFACT_ROOT=${CONTAINER_ARTIFACT_DIR}" \
  -e "SCBS_MAPPING_DECISION_MANIFEST=/mnt/${HOST_ARTIFACT_DIR}/scbs_mapping_decision_split_workbooks_manifest_v1.csv" \
  "${CONTAINER}" \
  odoo shell -c "${CONFIG}" -d "${DB}" < scripts/migration/scbs_mapping_decision_batch_validate.py
copy_from_container scbs_mapping_decision_batch_validate_result_v1.json
copy_from_container scbs_mapping_decision_batch_validate_summary_v1.csv

MIGRATION_ARTIFACT_ROOT="${HOST_ARTIFACT_DIR}" \
  python3 scripts/migration/scbs_mapping_decision_readiness_report.py

MIGRATION_ARTIFACT_ROOT="${HOST_ARTIFACT_DIR}" \
  python3 scripts/migration/scbs_mapping_decision_html_export.py

echo "SCBS mapping decision reports refreshed under ${HOST_ARTIFACT_DIR}"
