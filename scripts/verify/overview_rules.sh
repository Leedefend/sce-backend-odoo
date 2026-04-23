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
  echo "[verify.overview] FAIL item=$1 expected=$2 got=$3" >&2
  exit 1
}

check_eq() {
  local desc="$1" expected="$2" sql="$3"
  local val
  val="$(psql_cmd "${sql}")"
  if [[ "${val}" != "${expected}" ]]; then
    fail "${desc}" "${expected}" "${val}"
  else
    echo "[verify.overview] PASS item=${desc} value=${val}"
  fi
}

check_ge() {
  local desc="$1" min="$2" sql="$3"
  local val
  val="$(psql_cmd "${sql}")"
  if [[ -z "${val}" || "${val}" -lt "${min}" ]]; then
    fail "${desc}" ">=${min}" "${val}"
  else
    echo "[verify.overview] PASS item=${desc} value=${val}"
  fi
}

check_eq "next action rule model exists" "sc_project_next_action_rule" "SELECT to_regclass('sc_project_next_action_rule');"
check_eq "stage requirement item model exists" "sc_project_stage_requirement_item" "SELECT to_regclass('sc_project_stage_requirement_item');"
check_eq "stage requirement wizard line model exists" "sc_project_stage_requirement_wizard_line" "SELECT to_regclass('sc_project_stage_requirement_wizard_line');"

check_ge "next action rules (draft)" 1 "SELECT COUNT(*) FROM sc_project_next_action_rule WHERE lifecycle_state='draft' AND active IS TRUE;"
check_ge "next action rules (in_progress)" 1 "SELECT COUNT(*) FROM sc_project_next_action_rule WHERE lifecycle_state='in_progress' AND active IS TRUE;"
check_ge "stage requirements (draft)" 1 "SELECT COUNT(*) FROM sc_project_stage_requirement_item WHERE lifecycle_state='draft' AND active IS TRUE;"
check_ge "stage requirements (in_progress)" 1 "SELECT COUNT(*) FROM sc_project_stage_requirement_item WHERE lifecycle_state='in_progress' AND active IS TRUE;"

echo "[verify.overview] PASS ALL on ${DB_NAME}"
