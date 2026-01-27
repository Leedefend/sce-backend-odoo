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
  echo "[verify.overview.entry] FAIL item=$1 expected=$2 got=$3" >&2
  exit 1
}

check_eq() {
  local desc="$1" expected="$2" sql="$3"
  local val
  val="$(psql_cmd "${sql}")"
  if [[ "${val}" != "${expected}" ]]; then
    fail "${desc}" "${expected}" "${val}"
  else
    echo "[verify.overview.entry] PASS item=${desc} value=${val}"
  fi
}

menu_action=$(psql_cmd "SELECT m.action FROM ir_ui_menu m JOIN ir_model_data d ON d.res_id=m.id WHERE d.module='smart_construction_core' AND d.name='menu_sc_project_project';")
action_id=$(psql_cmd "SELECT res_id FROM ir_model_data WHERE module='smart_construction_core' AND name='action_sc_project_kanban_lifecycle';")
cap_menu_action=$(psql_cmd "SELECT m.action FROM ir_ui_menu m JOIN ir_model_data d ON d.res_id=m.id WHERE d.module='smart_construction_portal' AND d.name='menu_sc_portal_capability_matrix';")
cap_action_id=$(psql_cmd "SELECT res_id FROM ir_model_data WHERE module='smart_construction_portal' AND name='action_sc_portal_capability_matrix';")

check_eq "menu_sc_project_project action" "ir.actions.act_window,${action_id}" "SELECT m.action FROM ir_ui_menu m JOIN ir_model_data d ON d.res_id=m.id WHERE d.module='smart_construction_core' AND d.name='menu_sc_project_project';"
check_eq "action_sc_project_kanban_lifecycle exists" "${action_id}" "SELECT id FROM ir_act_window WHERE id=${action_id};"
check_eq "menu_sc_portal_capability_matrix action" "ir.actions.act_url,${cap_action_id}" "SELECT m.action FROM ir_ui_menu m JOIN ir_model_data d ON d.res_id=m.id WHERE d.module='smart_construction_portal' AND d.name='menu_sc_portal_capability_matrix';"
check_eq "action_sc_portal_capability_matrix exists" "${cap_action_id}" "SELECT id FROM ir_act_url WHERE id=${cap_action_id};"

view_mode=$(psql_cmd "SELECT view_mode FROM ir_act_window WHERE id=${action_id};")
echo "[verify.overview.entry] INFO action_sc_project_kanban_lifecycle view_mode=${view_mode}"
if [[ "${view_mode}" != *"kanban"* ]]; then
  fail "lifecycle kanban view mode" "contains kanban" "${view_mode}"
else
  echo "[verify.overview.entry] PASS item=lifecycle kanban view mode value=${view_mode}"
fi

echo "[verify.overview.entry] PASS ALL on ${DB_NAME}"
