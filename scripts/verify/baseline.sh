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

check_eq "lang zh_CN active" "1" "SELECT active::int FROM res_lang WHERE code='zh_CN';"
check_eq "admin lang" "zh_CN" "SELECT lang FROM res_partner WHERE id=(SELECT partner_id FROM res_users WHERE login='admin');"
check_eq "admin tz" "Asia/Shanghai" "SELECT tz FROM res_partner WHERE id=(SELECT partner_id FROM res_users WHERE login='admin');"
check_eq "company currency is CNY" "1" "SELECT 1 FROM res_company c JOIN res_currency rc ON c.currency_id=rc.id WHERE rc.name='CNY' LIMIT 1;"
check_eq "module smart_construction_bootstrap installed" "installed" "SELECT state FROM ir_module_module WHERE name='smart_construction_bootstrap';"

echo "[verify.baseline] PASS ALL on ${DB_NAME}"
