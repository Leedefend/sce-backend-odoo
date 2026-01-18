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

: "${DB_NAME:?DB_NAME is required}"

guard_prod_forbid

printf '[demo.verify] db=%s\n' "$DB_NAME"

scenario="${SCENARIO:-}"
step="${STEP:-}"
known="s00_min_path s10_contract_payment s20_settlement_clearing s30_settlement_workflow s40_failure_paths s50_repairable_paths s90_users_roles showroom"

if [ -n "$scenario" ]; then
  found=0
  for s in $known; do
    if [ "$scenario" = "$s" ]; then
      found=1
      break
    fi
  done
  if [ $found -eq 0 ]; then
    echo "ERROR: unknown SCENARIO '$scenario'. known: $known"
    exit 2
  fi
fi

psql_cmd() {
  compose_dev exec -T db psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 "$@" </dev/null
}

run_check() {
  desc="$1"; scen="$2"; ok_sql="$3"; sample_sql="$4"
  if [ -n "$scenario" ] && [ "$scenario" != "$scen" ]; then
    return 0
  fi
  if psql_cmd -At -c "$ok_sql" | grep -qx ok; then
    echo "✓ $desc"
    return 0
  fi
  echo "✗ $desc"
  if [ -n "$sample_sql" ]; then
    echo "[sample]"
    psql_cmd -c "$sample_sql" || true
    echo "[/sample]"
  fi
  exit 1
}

run_expect_fail() {
  desc="$1"; scen="$2"; ok_sql="$3"; sample_sql="$4"
  if [ "$scenario" != "$scen" ] || [ "$step" != "bad" ]; then
    return 0
  fi
  if psql_cmd -At -c "$ok_sql" | grep -qx ok; then
    echo "✗ $desc (expected failure)"
    if [ -n "$sample_sql" ]; then
      echo "[sample]"
      psql_cmd -c "$sample_sql" || true
      echo "[/sample]"
    fi
    exit 1
  fi
  echo "✗ $desc (bad condition missing)"
  exit 1
}

run_check "S00 projects >= 2" "s00_min_path" \
  "select case when count(*) >= 2 then 'ok' else 'project < 2' end from project_project;" \
  "select id, name from project_project order by id limit 20;"
run_check "S00 BOQ nodes >= 2" "s00_min_path" \
  "select case when count(*) >= 2 then 'ok' else 'boq < 2' end from project_boq_line;" \
  "select id, name, project_id, parent_id from project_boq_line order by id limit 20;"
run_check "S00 material plans >= 1" "s00_min_path" \
  "select case when count(*) >= 1 then 'ok' else 'material plan < 1' end from project_material_plan;" \
  "select id, name, project_id from project_material_plan order by id limit 20;"
run_check "S00 invoices >= 2" "s00_min_path" \
  "select case when count(*) >= 2 then 'ok' else 'invoice < 2' end from account_move where move_type in ('out_invoice','out_refund');" \
  "select id, name, state, move_type, invoice_date from account_move where move_type in ('out_invoice','out_refund') order by id limit 20;"
run_check "S10 contract record exists" "s10_contract_payment" \
  "select case when count(*) = 1 then 'ok' else 'S10 contract missing' end from construction_contract where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_contract_out_010');" \
  "select id, subject, type, project_id, partner_id from construction_contract where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_contract_out_010');"
run_check "S10 payment request record exists" "s10_contract_payment" \
  "select case when count(*) = 1 then 'ok' else 'S10 payment request missing' end from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_pay_req_010_001');" \
  "select id, type, amount, project_id, contract_id, partner_id, settlement_id from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_pay_req_010_001');"
run_check "S10 invoices >= 2" "s10_contract_payment" \
  "select case when count(*) >= 2 then 'ok' else 'S10 invoices < 2' end from account_move where id in (select res_id from ir_model_data where module='smart_construction_demo' and name in ('sc_demo_invoice_s10_001','sc_demo_invoice_s10_002'));" \
  "select id, name, state, move_type, invoice_date, amount_total from account_move where id in (select res_id from ir_model_data where module='smart_construction_demo' and name in ('sc_demo_invoice_s10_001','sc_demo_invoice_s10_002')) order by id;"
run_check "S20 payment record exists" "s20_settlement_clearing" \
  "select case when count(*) = 1 then 'ok' else 'S20 payment missing' end from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_020_001');" \
  "select id, type, amount, project_id, contract_id, partner_id, settlement_id from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_020_001');"
run_check "S20 settlement order exists" "s20_settlement_clearing" \
  "select case when count(*) = 1 then 'ok' else 'S20 settlement missing' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_020_001');" \
  "select id, name, state, amount_total, settlement_type from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_020_001');"
run_check "S20 settlement lines >= 2" "s20_settlement_clearing" \
  "select case when count(*) >= 2 then 'ok' else 'S20 settlement lines < 2' end from sc_settlement_order_line where id in (select res_id from ir_model_data where module='smart_construction_demo' and name in ('sc_demo_settle_line_020_001','sc_demo_settle_line_020_002'));" \
  "select id, settlement_id, name, qty, price_unit, amount from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_020_001') order by id;"
run_check "S20 settlement links to at least 1 payment request" "s20_settlement_clearing" \
  "select case when count(*) >= 1 then 'ok' else 'S20 settlement has no linked payment_request' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_020_001');" \
  "select id, type, amount, settlement_id from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_020_001') order by id;"
run_check "S30 settlement exists and stays in draft" "s30_settlement_workflow" \
  "select case when count(*) = 1 then 'ok' else 'S30 settlement missing or not draft' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001') and state = 'draft';" \
  "select id, name, state, amount_total, settlement_type from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001');"
run_check "S30 settlement has at least one line" "s30_settlement_workflow" \
  "select case when count(*) >= 1 then 'ok' else 'S30 settlement has no lines' end from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001');" \
  "select id, settlement_id, name, amount from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001') order by id;"
run_check "S30 settlement links to payment requests" "s30_settlement_workflow" \
  "select case when count(*) >= 1 then 'ok' else 'S30 settlement has no linked payment_request' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001');" \
  "select id, type, amount, settlement_id from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001') order by id;"
run_check "S30 settlement amount matches line sum" "s30_settlement_workflow" \
  "select case when abs(o.amount_total - sum(l.amount)) < 0.01 then 'ok' else 'S30 settlement amount mismatch' end from sc_settlement_order o join sc_settlement_order_line l on l.settlement_id = o.id where o.id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001') group by o.amount_total;" \
  "select o.id, o.amount_total, sum(l.amount) as line_sum from sc_settlement_order o join sc_settlement_order_line l on l.settlement_id = o.id where o.id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001') group by o.id, o.amount_total;"
run_check "S30 gate: bad settlement stays draft" "s30_settlement_workflow" \
  "select case when count(*) = 1 then 'ok' else 'S30 gate failed' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_bad_001') and state = 'draft';" \
  "select id, name, state from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_bad_001');"
run_check "S40 structural settlement stays draft" "s40_failure_paths" \
  "select case when count(*) = 1 then 'ok' else 'S40 structural missing or not draft' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_structural_bad') and state = 'draft';" \
  "select id, name, state from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_structural_bad');"
run_check "S40 structural has no lines" "s40_failure_paths" \
  "select case when count(*) = 0 then 'ok' else 'S40 structural has lines' end from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_structural_bad');" \
  "select id, settlement_id, name, amount from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_structural_bad');"
run_check "S40 structural has no payment requests" "s40_failure_paths" \
  "select case when count(*) = 0 then 'ok' else 'S40 structural has payment requests' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_structural_bad');" \
  "select id, amount, settlement_id from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_structural_bad');"
run_check "S40 amount mismatch stays draft" "s40_failure_paths" \
  "select case when count(*) = 1 then 'ok' else 'S40 amount missing or not draft' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad') and state = 'draft';" \
  "select id, name, state, amount_total from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad');"
run_check "S40 amount has lines" "s40_failure_paths" \
  "select case when count(*) >= 1 then 'ok' else 'S40 amount has no lines' end from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad');" \
  "select id, settlement_id, name, amount from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad') order by id;"
run_check "S40 amount links payment request" "s40_failure_paths" \
  "select case when count(*) >= 1 then 'ok' else 'S40 amount has no payment request' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad');" \
  "select id, amount, settlement_id from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad');"
run_check "S40 amount inconsistency (payment > settlement)" "s40_failure_paths" \
  "select case when (select coalesce(sum(pr.amount), 0) from payment_request pr where pr.settlement_id = (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad')) > (select amount_total from sc_settlement_order where id = (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad')) then 'ok' else 'S40 amount not inconsistent' end;" \
  "select (select amount_total from sc_settlement_order where id = (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad')) as settlement_total, (select coalesce(sum(pr.amount), 0) from payment_request pr where pr.settlement_id = (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad')) as payment_total;"
run_check "S40 link bad stays draft" "s40_failure_paths" \
  "select case when count(*) = 1 then 'ok' else 'S40 link missing or not draft' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_link_bad') and state = 'draft';" \
  "select id, name, state from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_link_bad');"
run_check "S40 link bad has lines" "s40_failure_paths" \
  "select case when count(*) >= 1 then 'ok' else 'S40 link has no lines' end from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_link_bad');" \
  "select id, settlement_id, name, amount from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_link_bad') order by id;"
run_check "S40 link bad has no linked payment request" "s40_failure_paths" \
  "select case when count(*) = 0 then 'ok' else 'S40 link unexpectedly linked' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_link_bad');" \
  "select id, amount, settlement_id from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_link_bad');"
run_check "S40 unlinked payment request exists" "s40_failure_paths" \
  "select case when count(*) = 1 then 'ok' else 'S40 unlinked payment missing' end from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_040_link_001') and settlement_id is null;" \
  "select id, amount, settlement_id from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_040_link_001');"
run_check "S40 settlements never leave draft" "s40_failure_paths" \
  "select case when count(*) = 0 then 'ok' else 'S40 settlement advanced' end from sc_settlement_order where name like 'S40-%' and state <> 'draft';" \
  "select id, name, state from sc_settlement_order where name like 'S40-%' and state <> 'draft' order by id;"
run_expect_fail "S50 bad seed should fail verification" "s50_repairable_paths" \
  "select case when count(*) = 0 then 'ok' else 'S50 bad still linked' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_050_001');" \
  "select id, amount, settlement_id from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_050_001');"
run_check "S50 settlement links payment request after fix" "s50_repairable_paths" \
  "select case when count(*) = 1 then 'ok' else 'S50 payment not linked' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_050_001');" \
  "select id, amount, settlement_id from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_050_001');"
run_check "S90 users exist" "s90_users_roles" \
  "select case when count(*) >= 5 then 'ok' else 'S90 users missing' end from res_users where login in ('demo_pm','demo_finance','demo_cost','demo_audit','demo_readonly');" \
  "select id, login, active from res_users where login in ('demo_pm','demo_finance','demo_cost','demo_audit','demo_readonly') order by login;"
run_check "S90 finance user lacks contract capability" "s90_users_roles" \
  "select case when count(*) = 0 then 'ok' else 'S90 finance has contract group' end from res_groups_users_rel r where r.uid = (select id from res_users where login='demo_finance') and r.gid in (select id from res_groups where coalesce(name->>'zh_CN', name->>'en_US') like 'SC 能力 - 合同中心%');" \
  "select u.login, coalesce(g.name->>'zh_CN', g.name->>'en_US') as group_name from res_groups_users_rel r join res_users u on u.id = r.uid join res_groups g on g.id = r.gid where u.login='demo_finance' order by group_name;"
run_check "S90 readonly user not in settlement user group" "s90_users_roles" \
  "select case when count(*) = 0 then 'ok' else 'S90 readonly has settlement group' end from res_groups_users_rel r where r.uid = (select id from res_users where login='demo_readonly') and r.gid in (select id from res_groups where coalesce(name->>'zh_CN', name->>'en_US') = 'SC 能力 - 结算中心经办');" \
  "select u.login, coalesce(g.name->>'zh_CN', g.name->>'en_US') as group_name from res_groups_users_rel r join res_users u on u.id = r.uid join res_groups g on g.id = r.gid where u.login='demo_readonly' order by group_name;"
run_check "showroom projects >= 8" "showroom" \
  "select case when count(*) >= 8 then 'ok' else 'showroom projects < 8' end from project_project where coalesce(name->>'zh_CN', name->>'en_US', name::text) like '展厅-%';" \
  "select id, name, lifecycle_state from project_project where coalesce(name->>'zh_CN', name->>'en_US', name::text) like '展厅-%' order by id;"
run_check "showroom tasks >= 80" "showroom" \
  "select case when count(*) >= 80 then 'ok' else 'showroom tasks < 80' end from project_task where project_id in (select id from project_project where coalesce(name->>'zh_CN', name->>'en_US', name::text) like '展厅-%');" \
  "select id, name, project_id from project_task where project_id in (select id from project_project where coalesce(name->>'zh_CN', name->>'en_US', name::text) like '展厅-%') order by id limit 20;"
run_check "showroom contracts >= 3" "showroom" \
  "select case when count(*) >= 3 then 'ok' else 'showroom contracts < 3' end from construction_contract where subject like '展厅合同-%';" \
  "select id, subject, project_id, state from construction_contract where subject like '展厅合同-%' order by id;"
run_check "showroom stages >= 4" "showroom" \
  "select case when count(distinct stage_id) >= 4 then 'ok' else 'showroom stages < 4' end from project_project where coalesce(name->>'zh_CN', name->>'en_US', name::text) like '展厅-%';" \
  "select stage_id, count(*) from project_project where coalesce(name->>'zh_CN', name->>'en_US', name::text) like '展厅-%' group by stage_id order by stage_id;"

run_check "showroom settlement projects in closing+" "showroom" \
  "select case when (select count(distinct p.id) from project_project p join sc_settlement_order s on s.project_id = p.id where coalesce(p.name->>'zh_CN', p.name->>'en_US', p.name::text) like '展厅-%') = (select count(distinct p.id) from project_project p join sc_settlement_order s on s.project_id = p.id join ir_model_data d on d.res_id = p.stage_id and d.model='project.project.stage' and d.module='smart_construction_core' where coalesce(p.name->>'zh_CN', p.name->>'en_US', p.name::text) like '展厅-%' and d.name in ('project_stage_closing','project_stage_closed','project_stage_warranty','project_stage_archived')) then 'ok' else 'showroom settlement stage mismatch' end;" \
  "select p.id, coalesce(p.name->>'zh_CN', p.name->>'en_US', p.name::text) as name, d.name as stage_xmlid from project_project p join sc_settlement_order s on s.project_id = p.id left join ir_model_data d on d.res_id = p.stage_id and d.model='project.project.stage' and d.module='smart_construction_core' where coalesce(p.name->>'zh_CN', p.name->>'en_US', p.name::text) like '展厅-%' order by p.id;"

echo "🎉 demo.verify PASSED"
