#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

: "${DB_NAME:?DB_NAME required}"
: "${DB_USER:?DB_USER required}"
: "${COMPOSE_FILES:?COMPOSE_FILES required}"

psql_cmd() {
  compose ${COMPOSE_FILES} exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -At -c "$1"
}

fail() {
  echo "[verify.overview.logic] FAIL item=$1 expected=$2 got=$3" >&2
  exit 1
}

check_eq() {
  local desc="$1" expected="$2" sql="$3"
  local val
  val="$(psql_cmd "${sql}")"
  if [[ "${val}" != "${expected}" ]]; then
    fail "${desc}" "${expected}" "${val}"
  else
    echo "[verify.overview.logic] PASS item=${desc} value=${val}"
  fi
}

# 1) Create entry view should point to minimal create form
create_view_id=$(psql_cmd "SELECT view_id FROM ir_act_window WHERE id=(SELECT res_id FROM ir_model_data WHERE module='smart_construction_core' AND name='action_project_initiation');")
create_view_xmlid=$(psql_cmd "SELECT module||'.'||name FROM ir_model_data WHERE res_id=${create_view_id} AND model='ir.ui.view' LIMIT 1;")
check_eq "project initiation view" "smart_construction_core.view_project_create_form" "SELECT module||'.'||name FROM ir_model_data WHERE res_id=${create_view_id} AND model='ir.ui.view' LIMIT 1;"

# 2) Menu groups for manage / stage requirement config
manage_menu_groups=$(psql_cmd "SELECT string_agg(gid::text, ',') FROM ir_ui_menu_group_rel WHERE menu_id=(SELECT res_id FROM ir_model_data WHERE module='smart_construction_core' AND name='menu_sc_project_manage');")
stage_menu_groups=$(psql_cmd "SELECT string_agg(gid::text, ',') FROM ir_ui_menu_group_rel WHERE menu_id=(SELECT res_id FROM ir_model_data WHERE module='smart_construction_core' AND name='menu_sc_project_stage_requirement_items');")
cap_menu_groups=$(psql_cmd "SELECT string_agg(gid::text, ',') FROM ir_ui_menu_group_rel WHERE menu_id=(SELECT res_id FROM ir_model_data WHERE module='smart_construction_portal' AND name='menu_sc_portal_capability_matrix');")
cap_action_url=$(psql_cmd "SELECT url FROM ir_act_url WHERE id=(SELECT res_id FROM ir_model_data WHERE module='smart_construction_portal' AND name='action_sc_portal_capability_matrix');")

if [[ -z "${manage_menu_groups}" ]]; then
  fail "project manage menu groups" "non-empty" "empty"
else
  echo "[verify.overview.logic] PASS item=project manage menu groups value=${manage_menu_groups}"
fi
if [[ -z "${stage_menu_groups}" ]]; then
  fail "stage requirement menu groups" "non-empty" "empty"
else
  echo "[verify.overview.logic] PASS item=stage requirement menu groups value=${stage_menu_groups}"
fi

if [[ -z "${cap_menu_groups}" ]]; then
  fail "capability matrix menu groups" "non-empty" "empty"
else
  echo "[verify.overview.logic] PASS item=capability matrix menu groups value=${cap_menu_groups}"
fi

check_eq "capability matrix action url" "/portal/capability-matrix" "SELECT url FROM ir_act_url WHERE id=(SELECT res_id FROM ir_model_data WHERE module='smart_construction_portal' AND name='action_sc_portal_capability_matrix');"

echo "[verify.overview.logic] PASS ALL on ${DB_NAME}"
