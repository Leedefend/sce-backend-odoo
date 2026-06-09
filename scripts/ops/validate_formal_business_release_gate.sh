#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

DB_NAME="${DB_NAME:-${DB:-sc_demo}}"

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME is required}"

ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH:-/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux}"
DB_PASSWORD="${DB_PASSWORD:-${DB_USER}}"

run_odoo_shell_check() {
  local name="$1"
  local script="$2"
  local output_file
  output_file="$(mktemp)"
  echo "FORMAL_BUSINESS_RELEASE_GATE_CHECK_START: ${name}"
  compose_dev exec -T \
    -e PYTHONWARNINGS=ignore \
    odoo odoo shell -d "$DB_NAME" \
    --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
    --addons-path="$ODOO_ADDONS_PATH" \
    --logfile=/dev/null --log-level=warn \
    < "$ROOT_DIR/$script" | tee "$output_file"
  local child_status="${PIPESTATUS[0]}"
  if [[ "$child_status" -ne 0 ]]; then
    rm -f "$output_file"
    return "$child_status"
  fi
  local summary_status
  summary_status="$(
    grep -E '^\{.*"status"' "$output_file" | tail -n 1 | jq -r '.status // empty'
  )"
  rm -f "$output_file"
  if [[ "$summary_status" != "PASS" ]]; then
    echo "FORMAL_BUSINESS_RELEASE_GATE_CHECK_FAIL: ${name} status=${summary_status:-missing}"
    return 1
  fi
  echo "FORMAL_BUSINESS_RELEASE_GATE_CHECK_PASS: ${name}"
}

started_at="$(date -Iseconds)"
echo "FORMAL_BUSINESS_RELEASE_GATE_START: db=${DB_NAME} started_at=${started_at}"

run_odoo_shell_check "user_confirmed_menu_surface" "scripts/verify/user_confirmed_menu_surface_guard.py"
run_odoo_shell_check "user_confirmed_form_capability" "scripts/verify/user_confirmed_form_capability_audit.py"
run_odoo_shell_check "user_confirmed_form_data_alignment" "scripts/verify/user_confirmed_form_data_alignment_audit.py"
run_odoo_shell_check "user_confirmed_settlement_usability" "scripts/verify/user_confirmed_settlement_usability_audit.py"

echo "FORMAL_BUSINESS_RELEASE_GATE_CHECK_START: business_capability"
DB_NAME="$DB_NAME" "$ROOT_DIR/scripts/ops/validate_business_capability_gate.sh"
echo "FORMAL_BUSINESS_RELEASE_GATE_CHECK_PASS: business_capability"

finished_at="$(date -Iseconds)"
echo "FORMAL_BUSINESS_RELEASE_GATE_RESULT: PASS db=${DB_NAME} started_at=${started_at} finished_at=${finished_at}"
