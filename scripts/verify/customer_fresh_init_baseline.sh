#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME is required}"

DB_PASSWORD="${DB_PASSWORD:-${DB_USER}}"
CUSTOMER_COMPANY_NAME="${CUSTOMER_COMPANY_NAME:-四川保盛建设集团有限公司}"
CUSTOMER_CURRENCY="${CUSTOMER_CURRENCY:-CNY}"

SEED_LOGINS=(
  wutao
  yangdesheng
  zhangwencui
  lijianfeng
  yelingyue
  lidexue
  chenshuai
)

psql_query() {
  local sql="$1"
  compose_dev exec -T -e PGPASSWORD="$DB_PASSWORD" db \
    psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -F $'\t' -Atc "$sql"
}

sql_literal() {
  printf "'%s'" "${1//\'/\'\'}"
}

fail() {
  echo "[verify.customer_fresh_init] FAIL item=$1 expected=$2 got=$3" >&2
  exit 1
}

pass() {
  echo "[verify.customer_fresh_init] PASS item=$1 value=$2"
}

check_eq() {
  local item="$1"
  local expected="$2"
  local sql="$3"
  local got
  got="$(psql_query "$sql")"
  if [[ "$got" != "$expected" ]]; then
    fail "$item" "$expected" "${got:-<empty>}"
  fi
  pass "$item" "$got"
}

login_sql_list() {
  local out=""
  local login
  for login in "${SEED_LOGINS[@]}"; do
    if [[ -n "$out" ]]; then
      out+=","
    fi
    out+="$(sql_literal "$login")"
  done
  printf "%s" "$out"
}

LOGIN_LIST="$(login_sql_list)"
COMPANY_NAME_SQL="$(sql_literal "$CUSTOMER_COMPANY_NAME")"
CURRENCY_SQL="$(sql_literal "$CUSTOMER_CURRENCY")"

echo "[verify.customer_fresh_init] db=${DB_NAME}"

check_eq "module base installed" "installed" \
  "SELECT state FROM ir_module_module WHERE name='base';"
check_eq "module smart_construction_bootstrap installed" "installed" \
  "SELECT state FROM ir_module_module WHERE name='smart_construction_bootstrap';"
check_eq "module smart_construction_custom installed" "installed" \
  "SELECT state FROM ir_module_module WHERE name='smart_construction_custom';"
check_eq "module smart_construction_demo not installed" "0" \
  "SELECT COUNT(*) FROM ir_module_module WHERE name='smart_construction_demo' AND state='installed';"

check_eq "base.main_company points to company 1" "1" \
  "SELECT res_id FROM ir_model_data WHERE module='base' AND name='main_company' AND model='res.company';"
check_eq "main company customer name" "$CUSTOMER_COMPANY_NAME" \
  "SELECT name FROM res_company WHERE id=1;"
check_eq "main company currency" "$CUSTOMER_CURRENCY" \
  "SELECT rc.name FROM res_company c JOIN res_currency rc ON rc.id=c.currency_id WHERE c.id=1;"
check_eq "main company active" "t" \
  "SELECT active FROM res_company WHERE id=1;"
check_eq "no active My Company" "0" \
  "SELECT COUNT(*) FROM res_company WHERE active IS TRUE AND name='My Company';"
check_eq "no active duplicate customer company" "1" \
  "SELECT COUNT(*) FROM res_company WHERE active IS TRUE AND name=${COMPANY_NAME_SQL};"

check_eq "seed user count" "${#SEED_LOGINS[@]}" \
  "SELECT COUNT(*) FROM res_users WHERE login IN (${LOGIN_LIST});"
check_eq "seed users main company" "0" \
  "SELECT COUNT(*) FROM res_users WHERE login IN (${LOGIN_LIST}) AND company_id <> 1;"
check_eq "seed users only main company scope" "0" \
  "SELECT COUNT(*)
     FROM res_users u
    WHERE u.login IN (${LOGIN_LIST})
      AND EXISTS (
        SELECT 1
          FROM res_company_users_rel rel
         WHERE rel.user_id = u.id
         GROUP BY rel.user_id
        HAVING COUNT(*) <> 1 OR MIN(rel.cid) <> 1 OR MAX(rel.cid) <> 1
      );"
check_eq "seed users can resolve company currency" "${#SEED_LOGINS[@]}" \
  "SELECT COUNT(*)
     FROM res_users u
     JOIN res_company c ON c.id = u.company_id
     JOIN res_currency rc ON rc.id = c.currency_id
    WHERE u.login IN (${LOGIN_LIST})
      AND c.id = 1
      AND c.name = ${COMPANY_NAME_SQL}
      AND rc.name = ${CURRENCY_SQL};"

check_eq "default sale tax xmlid active" "1" \
  "SELECT COUNT(*)
     FROM ir_model_data d
     JOIN account_tax t ON t.id = d.res_id
    WHERE d.module='smart_construction_seed'
      AND d.name='tax_sale_9'
      AND d.model='account.tax'
      AND t.company_id=1
      AND COALESCE(t.name->>'zh_CN', t.name->>'en_US')='销项VAT 9%'
      AND t.amount=9.0
      AND t.amount_type='percent'
      AND t.type_tax_use='sale'
      AND t.price_include IS FALSE
      AND t.active IS TRUE;"
check_eq "default purchase tax xmlid active" "1" \
  "SELECT COUNT(*)
     FROM ir_model_data d
     JOIN account_tax t ON t.id = d.res_id
    WHERE d.module='smart_construction_seed'
      AND d.name='tax_purchase_13'
      AND d.model='account.tax'
      AND t.company_id=1
      AND COALESCE(t.name->>'zh_CN', t.name->>'en_US')='进项VAT 13%'
      AND t.amount=13.0
      AND t.amount_type='percent'
      AND t.type_tax_use='purchase'
      AND t.price_include IS FALSE
      AND t.active IS TRUE;"

echo "[verify.customer_fresh_init] PASS ALL on ${DB_NAME}"
