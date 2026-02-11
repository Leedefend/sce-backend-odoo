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
  val="$(psql_cmd "SELECT 1 FROM res_company c JOIN res_currency rc ON c.currency_id=rc.id WHERE rc.name='CNY' LIMIT 1;")"
  if [[ "${val}" == "1" ]]; then
    echo "[verify.baseline] PASS item=company currency is CNY value=1"
    return
  fi

  if ! autofix_enabled; then
    fail "company currency is CNY" "1" "${val:-<empty>} (hint: BASELINE_AUTO_FIX=1 make verify.baseline DB_NAME=${DB_NAME})"
  fi

  echo "[verify.baseline] FIX item=company currency -> CNY"
  local cny_id
  cny_id="$(psql_cmd "SELECT id FROM res_currency WHERE name='CNY' LIMIT 1;")"
  if [[ -z "${cny_id}" ]]; then
    fail "company currency is CNY" "CNY currency record exists" "<missing>"
  fi

  psql_cmd "UPDATE res_currency SET active=TRUE WHERE id=${cny_id};" >/dev/null
  psql_cmd "UPDATE res_company SET currency_id=${cny_id} WHERE currency_id IS DISTINCT FROM ${cny_id};" >/dev/null

  val="$(psql_cmd "SELECT 1 FROM res_company c JOIN res_currency rc ON c.currency_id=rc.id WHERE rc.name='CNY' LIMIT 1;")"
  if [[ "${val}" != "1" ]]; then
    fail "company currency is CNY" "1" "${val:-<empty>} (after auto-fix)"
  fi
  echo "[verify.baseline] PASS item=company currency is CNY value=1 (auto-fixed)"
}

check_eq "lang zh_CN active" "1" "SELECT active::int FROM res_lang WHERE code='zh_CN';"
check_eq "admin lang" "zh_CN" "SELECT lang FROM res_partner WHERE id=(SELECT partner_id FROM res_users WHERE login='admin');"
check_eq "admin tz" "Asia/Shanghai" "SELECT tz FROM res_partner WHERE id=(SELECT partner_id FROM res_users WHERE login='admin');"
check_company_currency_cny
check_eq "module smart_construction_bootstrap installed" "installed" "SELECT state FROM ir_module_module WHERE name='smart_construction_bootstrap';"

echo "[verify.baseline] PASS ALL on ${DB_NAME}"
