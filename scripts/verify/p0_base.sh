#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

: "${DB_NAME:?DB_NAME required}"
: "${DB_USER:?DB_USER required}"
: "${COMPOSE_FILES:?COMPOSE_FILES required}"

DB_PASSWORD=${DB_PASSWORD:-${DB_USER}}

psql_cmd() {
  compose ${COMPOSE_FILES} exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -At -c "$1"
}

fail() {
  echo "[verify.p0] FAIL item=$1 expected=$2 got=$3" >&2
  exit 1
}

check_eq() {
  local desc="$1" expected="$2" sql="$3"
  local val
  val="$(psql_cmd "${sql}")"
  if [[ "${val}" != "${expected}" ]]; then
    fail "${desc}" "${expected}" "${val}"
  else
    echo "[verify.p0] PASS item=${desc} value=${val}"
  fi
}

check_ge() {
  local desc="$1" expected="$2" sql="$3"
  local val
  val="$(psql_cmd "${sql}")"
  if [[ "${val}" -lt "${expected}" ]]; then
    fail "${desc}" ">=${expected}" "${val}"
  else
    echo "[verify.p0] PASS item=${desc} value=${val}"
  fi
}

check_eq "module core installed" "installed" "SELECT state FROM ir_module_module WHERE name='smart_construction_core';"
check_eq "module seed installed" "installed" "SELECT state FROM ir_module_module WHERE name='smart_construction_seed';"

check_eq "login custom enabled" "1" "SELECT value FROM ir_config_parameter WHERE key='sc.login.custom_enabled';"
check_eq "workbench enabled" "1" "SELECT value FROM ir_config_parameter WHERE key='sc.workbench.enabled';"
check_eq "workbench action xmlid" "smart_construction_core.action_sc_project_workbench" \
  "SELECT value FROM ir_config_parameter WHERE key='sc.workbench.default_action_xmlid';"
check_eq "sidebar overview enabled" "1" "SELECT value FROM ir_config_parameter WHERE key='sc.sidebar.overview_enabled';"
check_eq "sidebar overview menu ids" "265" "SELECT value FROM ir_config_parameter WHERE key='sc.sidebar.overview_menu_ids';"
check_eq "login env prod" "prod" "SELECT value FROM ir_config_parameter WHERE key='sc.login.env';"

check_ge "project stages (company-wide)" "5" "SELECT count(1) FROM project_project_stage WHERE company_id IS NULL;"
check_ge "project stages default" "1" "SELECT count(1) FROM project_project_stage WHERE company_id IS NULL AND is_default IS TRUE;"

check_ge "dict project_type" "1" "SELECT count(1) FROM sc_dictionary WHERE type='project_type' AND active IS TRUE;"
check_ge "dict project_category" "1" "SELECT count(1) FROM sc_dictionary WHERE type='project_category' AND active IS TRUE;"
check_ge "dict contract_category" "1" "SELECT count(1) FROM sc_dictionary WHERE type='contract_category' AND active IS TRUE;"
check_ge "dict contract_type" "1" "SELECT count(1) FROM sc_dictionary WHERE type='contract_type' AND active IS TRUE;"
check_ge "dict doc_type" "1" "SELECT count(1) FROM sc_dictionary WHERE type='doc_type' AND active IS TRUE;"
check_ge "dict doc_subtype" "1" "SELECT count(1) FROM sc_dictionary WHERE type='doc_subtype' AND active IS TRUE;"
check_ge "dict fee_type" "1" "SELECT count(1) FROM sc_dictionary WHERE type='fee_type' AND active IS TRUE;"
check_ge "dict tax_type" "1" "SELECT count(1) FROM sc_dictionary WHERE type='tax_type' AND active IS TRUE;"
check_ge "dict cost_item" "1" "SELECT count(1) FROM sc_dictionary WHERE type='cost_item' AND active IS TRUE;"

if [[ "${SC_BOOTSTRAP_USERS:-}" =~ ^(1|true|True|yes|YES)$ ]]; then
  BOOT_LOGIN="${SC_BOOTSTRAP_ADMIN_LOGIN:-pm_admin}"
  check_eq "bootstrap user exists" "1" "SELECT count(1) FROM res_users WHERE login='${BOOT_LOGIN}' AND active IS TRUE;"
fi

echo "[verify.p0] PASS ALL on ${DB_NAME}"
