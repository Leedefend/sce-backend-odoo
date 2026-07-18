#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

: "${DB_NAME:?DB_NAME required}"
: "${DB_USER:?DB_USER required}"
: "${COMPOSE_FILES:?COMPOSE_FILES required}"

DB_PASSWORD=${DB_PASSWORD:-${DB_USER}}
EXPECTED_CURRENCY="${SC_BASELINE_CURRENCY:-CNY}"

psql_cmd() {
  compose ${COMPOSE_FILES} exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -At -c "$1"
}

sql_literal() {
  local value="${1//\'/\'\'}"
  printf "'%s'" "$value"
}

fail() {
  echo "[verify.baseline] FAIL item=$1 expected=$2 got=$3" >&2
  exit 1
}

autofix_enabled() {
  [[ "${BASELINE_AUTO_FIX:-0}" == "1" ]]
}

check_eq() {
  local desc="$1" expected="$2" sql="$3"
  local val
  val="$(psql_cmd "${sql}")"
  if [[ "${val}" != "${expected}" ]]; then
    fail "${desc}" "${expected}" "${val}"
  else
    echo "[verify.baseline] PASS item=${desc} value=${val}"
  fi
}

check_company_currency_cny() {
  local val
  val="$(psql_cmd "SELECT rc.name
                    FROM ir_model_data imd
                    JOIN res_company c ON c.id=imd.res_id
                    JOIN res_currency rc ON c.currency_id=rc.id
                   WHERE imd.module='base' AND imd.name='main_company' AND imd.model='res.company'
                   LIMIT 1;")"
  if [[ "${val}" == "${EXPECTED_CURRENCY}" ]]; then
    echo "[verify.baseline] PASS item=main company currency value=${val}"
    return
  fi

  if ! autofix_enabled; then
    fail "main company currency" "${EXPECTED_CURRENCY}" "${val:-<empty>} (hint: BASELINE_AUTO_FIX=1 make verify.baseline DB_NAME=${DB_NAME})"
  fi

  echo "[verify.baseline] FIX item=main company currency -> ${EXPECTED_CURRENCY}"
  local cny_id
  cny_id="$(psql_cmd "SELECT id FROM res_currency WHERE name=$(sql_literal "${EXPECTED_CURRENCY}") LIMIT 1;")"
  if [[ -z "${cny_id}" ]]; then
    fail "main company currency" "${EXPECTED_CURRENCY} currency record exists" "<missing>"
  fi

  psql_cmd "UPDATE res_currency SET active=TRUE WHERE id=${cny_id};" >/dev/null
  psql_cmd "UPDATE res_company
               SET currency_id=${cny_id}
              WHERE id=(SELECT res_id FROM ir_model_data WHERE module='base' AND name='main_company' AND model='res.company' LIMIT 1)
                AND currency_id IS DISTINCT FROM ${cny_id};" >/dev/null

  val="$(psql_cmd "SELECT rc.name
                    FROM ir_model_data imd
                    JOIN res_company c ON c.id=imd.res_id
                    JOIN res_currency rc ON c.currency_id=rc.id
                   WHERE imd.module='base' AND imd.name='main_company' AND imd.model='res.company'
                   LIMIT 1;")"
  if [[ "${val}" != "${EXPECTED_CURRENCY}" ]]; then
    fail "main company currency" "${EXPECTED_CURRENCY}" "${val:-<empty>} (after auto-fix)"
  fi
  echo "[verify.baseline] PASS item=main company currency value=${val} (auto-fixed)"
}

check_eq "lang zh_CN active" "1" "SELECT active::int FROM res_lang WHERE code='zh_CN';"
check_eq "admin lang" "zh_CN" "SELECT lang FROM res_partner WHERE id=(SELECT partner_id FROM res_users WHERE login='admin');"
check_eq "admin tz" "Asia/Shanghai" "SELECT tz FROM res_partner WHERE id=(SELECT partner_id FROM res_users WHERE login='admin');"
check_company_currency_cny
check_eq "module smart_construction_bootstrap installed" "installed" "SELECT state FROM ir_module_module WHERE name='smart_construction_bootstrap';"

echo "[verify.baseline] PASS ALL on ${DB_NAME}"
