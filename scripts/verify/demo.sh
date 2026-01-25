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
  echo "[verify.demo] FAIL item=$1 expected=$2 got=$3" >&2
  exit 1
}


check_eq() {
  local desc="$1" expected="$2" sql="$3"
  local val
  val="$(psql_cmd "${sql}")"
  if [[ "${val}" != "${expected}" ]]; then
    fail "${desc}" "${expected}" "${val}"
  else
    echo "[verify.demo] PASS item=${desc} value=${val}"
  fi
}

# Baseline checks (reuse)
check_eq "lang zh_CN active" "1" "SELECT active::int FROM res_lang WHERE code='zh_CN';"
check_eq "admin lang" "zh_CN" "SELECT lang FROM res_partner WHERE id=(SELECT partner_id FROM res_users WHERE login='admin');"
check_eq "admin tz" "Asia/Shanghai" "SELECT tz FROM res_partner WHERE id=(SELECT partner_id FROM res_users WHERE login='admin');"
check_eq "company currency is CNY" "1" "SELECT 1 FROM res_company c JOIN res_currency rc ON c.currency_id=rc.id WHERE rc.name='CNY' LIMIT 1;"
check_eq "module smart_construction_bootstrap installed" "installed" "SELECT state FROM ir_module_module WHERE name='smart_construction_bootstrap';"

# Demo/seed specific
check_eq "module smart_construction_seed installed" "installed" "SELECT state FROM ir_module_module WHERE name='smart_construction_seed';"
check_eq "module smart_construction_demo installed" "installed" "SELECT state FROM ir_module_module WHERE name='smart_construction_demo';"
check_eq "seed execution flag" "1" "SELECT COALESCE((SELECT value FROM ir_config_parameter WHERE key='sc.seed.enabled'), '0');"
check_eq "seed last_steps contains sanity" "1" "SELECT ((POSITION('sanity' IN COALESCE((SELECT value FROM ir_config_parameter WHERE key='sc.seed.last_steps'), '')) > 0)::int);"
check_eq "seed sanity ran flag" "1" "SELECT COALESCE((SELECT value FROM ir_config_parameter WHERE key='sc.seed.sanity_ran'), '0');"
check_eq "seed dictionary marker" "1" "SELECT COALESCE((SELECT value FROM ir_config_parameter WHERE key='sc.seed.dictionary'), '0');"
check_eq "seed project skeleton marker" "1" "SELECT COALESCE((SELECT value FROM ir_config_parameter WHERE key='sc.seed.project_skeleton'), '0');"
check_eq "seed boq sample marker" "10" "SELECT COALESCE((SELECT value FROM ir_config_parameter WHERE key='sc.seed.boq_count'), '0');"
check_eq "seed metrics smoke marker" "1" "SELECT COALESCE((SELECT value FROM ir_config_parameter WHERE key='sc.seed.metrics_smoke'), '0');"
check_eq "seed tax sale exists" "1" "SELECT CASE WHEN COUNT(*) = 1 THEN '1' ELSE '0' END FROM account_tax t JOIN ir_model_data d ON d.res_id=t.id WHERE d.module='smart_construction_seed' AND d.name='tax_sale_9' AND t.active IS TRUE;"
check_eq "seed tax purchase exists" "1" "SELECT CASE WHEN COUNT(*) = 1 THEN '1' ELSE '0' END FROM account_tax t JOIN ir_model_data d ON d.res_id=t.id WHERE d.module='smart_construction_seed' AND d.name='tax_purchase_13' AND t.active IS TRUE;"
check_eq "seed partner contract exists" "1" "SELECT CASE WHEN COUNT(*) = 1 THEN '1' ELSE '0' END FROM res_partner WHERE name='Demo-合同相对方' AND active IS TRUE;"
check_eq "seed dict contract_type in exists" "1" "SELECT CASE WHEN COUNT(*) >= 1 THEN '1' ELSE '0' END FROM sc_dictionary WHERE type='contract_type' AND code='BASE_CONTRACT_IN' AND active IS TRUE;"
check_eq "seed dict contract_type out exists" "1" "SELECT CASE WHEN COUNT(*) >= 1 THEN '1' ELSE '0' END FROM sc_dictionary WHERE type='contract_type' AND code='BASE_CONTRACT_OUT' AND active IS TRUE;"
check_eq "seed dict contract_category exists" "1" "SELECT CASE WHEN COUNT(*) >= 1 THEN '1' ELSE '0' END FROM sc_dictionary WHERE type='contract_category' AND active IS TRUE;"
check_eq "demo users exist" "5" "SELECT COUNT(*)::text FROM res_users WHERE login IN ('demo_pm','demo_finance','demo_cost','demo_audit','demo_readonly') AND active IS TRUE AND share IS FALSE;"
check_eq "demo contracts exist" "1" "SELECT CASE WHEN COUNT(*) >= 1 THEN '1' ELSE '0' END FROM construction_contract WHERE project_id IS NOT NULL;"
check_eq "settlement order table exists" "sc_settlement_order" "SELECT to_regclass('sc_settlement_order');"
check_eq "demo settlement orders exist" "1" "SELECT CASE WHEN COUNT(*) >= 1 THEN '1' ELSE '0' END FROM sc_settlement_order WHERE name LIKE 'DEMO-SO-%' AND contract_id IS NOT NULL AND project_id IS NOT NULL;"
check_eq "demo settlement lines exist" "1" "SELECT CASE WHEN COUNT(*) >= 1 THEN '1' ELSE '0' END FROM sc_settlement_order_line l JOIN sc_settlement_order s ON s.id=l.settlement_id WHERE s.name LIKE 'DEMO-SO-%' AND l.amount > 0;"
check_eq "demo settlement amount_total positive" "1" "SELECT CASE WHEN COUNT(*) >= 1 THEN '1' ELSE '0' END FROM sc_settlement_order WHERE name LIKE 'DEMO-SO-%' AND amount_total > 0;"
check_eq "payment request table exists" "payment_request" "SELECT to_regclass('payment_request');"
check_eq "demo payment requests exist" "1" "SELECT CASE WHEN COUNT(*) >= 1 THEN '1' ELSE '0' END FROM payment_request WHERE name LIKE 'DEMO-PR-%' AND type='pay' AND project_id IS NOT NULL AND contract_id IS NOT NULL AND settlement_id IS NOT NULL;"
check_eq "demo payment within settlement remaining" "1" "SELECT CASE WHEN COUNT(*) >= 1 THEN '1' ELSE '0' END FROM payment_request pr JOIN sc_settlement_order s ON s.id=pr.settlement_id WHERE pr.name LIKE 'DEMO-PR-%' AND pr.amount <= s.remaining_amount;"


echo "[verify.demo] PASS ALL on ${DB_NAME}"
