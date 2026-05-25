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
known="s00_min_path s10_contract_payment s20_settlement_clearing s30_settlement_workflow s40_failure_paths s50_repairable_paths s65_cost_budget_funding_surface s66_ledger_entity_surface s67_scene_pack_surface s68_cockpit_workbench_surface s69_payment_ledger_surface s70_daily_business_surface s71_governance_audit_surface s72_project_governance_surface s73_risk_settlement_surface s74_partner_supplier_surface s75_summary_projection_surface s76_workflow_compat_surface s80_execution_management_surface s85_admin_finance_surface s86_tender_rental_finance_surface s87_resource_contract_surface s88_output_invoice_surface s89_quality_safety_surface s90_users_roles showroom"

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
run_check "S65 cost budget and allocation records exist" "s65_cost_budget_funding_surface" \
  "select case when (select count(*) from project_budget where name='S65 主体结构成本控制版' and version='S65-CTRL-V1') = 1 and (select count(*) from project_budget_boq_line where name='三层梁板钢筋制安') = 1 and (select count(*) from project_budget_cost_alloc where budget_boq_line_id in (select id from project_budget_boq_line where name='三层梁板钢筋制安')) = 2 then 'ok' else 'S65 budget records missing' end;" \
  "select b.id, b.name, b.version, b.amount_revenue_target, b.amount_cost_target from project_budget b where b.name='S65 主体结构成本控制版';"
run_check "S65 cost ledger progress and funding records exist" "s65_cost_budget_funding_surface" \
  "select case when (select count(*) from construction_work_breakdown where code in ('S65-01','S65-0101')) = 2 and (select count(*) from project_cost_period where period='2025-08' and locked=false) >= 1 and (select count(*) from project_cost_ledger where note='S65 钢筋材料成本入账样例。') = 1 and (select count(*) from project_progress_entry where note='S65 三层梁板钢筋本期进度计量草稿。' and state='draft') = 1 and (select count(*) from project_funding_baseline where total_amount=5000000.0 and state='active') = 1 then 'ok' else 'S65 cost ledger/progress/funding missing' end;" \
  "select 'cost_ledger' as kind, id, note, amount::text as value from project_cost_ledger where note='S65 钢筋材料成本入账样例。' union all select 'progress', id, note, progress_rate::text from project_progress_entry where note='S65 三层梁板钢筋本期进度计量草稿。' union all select 'funding', id, state, total_amount::text from project_funding_baseline where total_amount=5000000.0;"
run_check "S66 receipt invoice and output ledger records exist" "s66_ledger_entity_surface" \
  "select case when (select count(*) from sc_receipt_invoice_line where legacy_invoice_line_id='S66-RIL-001') = 1 and (select count(*) from sc_output_invoice_ledger where invoice_no='S66-RINV-NO-001' and source_model='sc.receipt.invoice.line') = 1 then 'ok' else 'S66 receipt invoice ledger missing' end;" \
  "select id, invoice_no, source_model, invoice_amount, current_receipt_amount from sc_output_invoice_ledger where invoice_no='S66-RINV-NO-001';"
run_check "S66 contract ledger records exist" "s66_ledger_entity_surface" \
  "select case when (select count(*) from sc_income_contract_ledger where contract_no='S66-GC-IN-NO-001') = 1 and (select count(*) from sc_expense_contract_ledger where contract_no='S66-GC-EX-NO-001') = 1 then 'ok' else 'S66 contract ledger missing' end;" \
  "select 'income' as kind, id, contract_no, contract_name, amount_total from sc_income_contract_ledger where contract_no='S66-GC-IN-NO-001' union all select 'expense', id, contract_no, contract_name, amount_total from sc_expense_contract_ledger where contract_no='S66-GC-EX-NO-001';"
run_check "S66 business entity mappings exist" "s66_ledger_entity_surface" \
  "select case when (select count(*) from sc_business_entity where name='S66 德阳项目经营载体' and mapping_state='confirmed') = 1 and (select count(*) from sc_legacy_business_entity_map where legacy_xmid='S66-XMID-001' and mapping_state='confirmed') = 1 and (select count(*) from sc_legacy_project_map where source_table='S66_SCBS_PROJECT_CANDIDATE' and mapping_state='confirmed') = 1 and (select count(*) from sc_legacy_partner_map where legacy_key='S66-PARTNER-OWNER-001' and mapping_state='confirmed') = 1 then 'ok' else 'S66 business entity mappings missing' end;" \
  "select 'entity' as kind, id, name, mapping_state from sc_business_entity where name='S66 德阳项目经营载体' union all select 'entity_map', id, legacy_xmmc, mapping_state from sc_legacy_business_entity_map where legacy_xmid='S66-XMID-001' union all select 'project_map', id, legacy_gcmc, mapping_state from sc_legacy_project_map where source_table='S66_SCBS_PROJECT_CANDIDATE' union all select 'partner_map', id, legacy_partner_name, mapping_state from sc_legacy_partner_map where legacy_key='S66-PARTNER-OWNER-001';"
run_check "S67 scene capability records exist" "s67_scene_pack_surface" \
  "select case when (select count(*) from sc_capability_group where key='demo_ops_surface') = 1 and (select count(*) from sc_capability where key='demo.ops.dashboard' and status='ga') = 1 and (select count(*) from sc_scene where code='s67_demo_ops_scene' and state='published') = 1 and (select count(*) from sc_scene_tile where scene_id in (select id from sc_scene where code='s67_demo_ops_scene')) = 1 and (select count(*) from sc_scene_version where scene_id in (select id from sc_scene where code='s67_demo_ops_scene') and version='v1.0') = 1 then 'ok' else 'S67 scene capability records missing' end;" \
  "select s.id, s.code, s.state, s.version, v.id as version_id from sc_scene s left join sc_scene_version v on v.id = s.active_version_id where s.code='s67_demo_ops_scene';"
run_check "S67 pack registry records exist" "s67_scene_pack_surface" \
  "select case when (select count(*) from sc_pack_registry where pack_id='s67.demo.surface.pack' and channel='stable') = 1 and (select count(*) from sc_pack_installation where pack_id in (select id from sc_pack_registry where pack_id='s67.demo.surface.pack') and status='installed') = 1 then 'ok' else 'S67 pack records missing' end;" \
  "select r.id, r.pack_id, r.pack_version, i.status from sc_pack_registry r left join sc_pack_installation i on i.pack_id = r.id where r.pack_id='s67.demo.surface.pack';"
run_check "S68 dashboard cockpit facts exist" "s68_cockpit_workbench_surface" \
  "select case when (select count(*) from sc_dashboard_cockpit_fact where name like 'S68 %' and fact_type in ('fund_cockpit', 'cost_cockpit')) = 2 then 'ok' else 'S68 dashboard facts missing' end;" \
  "select id, name, fact_type, project_id, amount, metric_value, source_model, source_res_id, state from sc_dashboard_cockpit_fact where name like 'S68 %' order by id;"
run_check "S68 workbench items exist" "s68_cockpit_workbench_surface" \
  "select case when (select count(*) from sc_workbench_item where name like 'S68 %' and fact_type in ('my_todo', 'my_approval', 'recent_visit')) = 3 then 'ok' else 'S68 workbench items missing' end;" \
  "select id, name, fact_type, priority, todo_deadline, source_model, source_res_id, state from sc_workbench_item where name like 'S68 %' order by id;"
run_check "S69 payment ledger chain exists" "s69_payment_ledger_surface" \
  "select case when (select count(*) from sc_settlement_order where name='S69-PAY-SET-001' and state='approve') = 1 and (select count(*) from payment_request where name='S69-PAY-REQ-001' and state='approved') = 1 and (select count(*) from payment_ledger where ref='S69-PAY-LEDGER-001' and amount=120000.0) = 1 then 'ok' else 'S69 payment ledger chain missing' end;" \
  "select l.id, l.ref, l.amount, pr.name as request_name, pr.state as request_state, s.name as settlement_name, s.state as settlement_state from payment_ledger l join payment_request pr on pr.id = l.payment_request_id left join sc_settlement_order s on s.id = pr.settlement_id where l.ref='S69-PAY-LEDGER-001';"
run_check "S70 material catalog and price exist" "s70_daily_business_surface" \
  "select case when (select count(*) from sc_material_catalog where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_material_catalog_070_steel')) = 1 and (select count(*) from sc_material_price where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_material_price_070_steel_quote')) = 1 then 'ok' else 'S70 material records missing' end;" \
  "select c.id, c.name, p.unit_price from sc_material_catalog c left join sc_material_price p on p.material_catalog_id = c.id where c.id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_material_catalog_070_steel');"
run_check "S70 finance daily records exist" "s70_daily_business_surface" \
  "select case when (select count(*) from sc_expense_claim where name='S70-EXP-001') = 1 and (select count(*) from sc_receipt_income where name='S70-RI-001') = 1 and (select count(*) from sc_payment_execution where name='S70-PE-001') = 1 and (select count(*) from sc_treasury_reconciliation where name='S70-TR-001') = 1 then 'ok' else 'S70 finance records missing' end;" \
  "select 'expense' as kind, id, name, state from sc_expense_claim where name='S70-EXP-001' union all select 'receipt', id, name, state from sc_receipt_income where name='S70-RI-001' union all select 'payment', id, name, state from sc_payment_execution where name='S70-PE-001' union all select 'treasury', id, name, state from sc_treasury_reconciliation where name='S70-TR-001';"
run_check "S70 invoice tax and diary records exist" "s70_daily_business_surface" \
  "select case when (select count(*) from sc_invoice_registration where name='S70-INV-001') = 1 and (select count(*) from sc_tax_deduction_registration where name='S70-TAX-001') = 1 and (select count(*) from sc_construction_diary where name='S70-DIARY-001') = 1 then 'ok' else 'S70 invoice/tax/diary records missing' end;" \
  "select 'invoice' as kind, id, name, state from sc_invoice_registration where name='S70-INV-001' union all select 'tax', id, name, state from sc_tax_deduction_registration where name='S70-TAX-001' union all select 'diary', id, name, state from sc_construction_diary where name='S70-DIARY-001';"
run_check "S71 approval governance seeds exist" "s71_governance_audit_surface" \
  "select case when (select count(*) from sc_approval_policy where code='payment_request_approval' and target_model='payment.request' and runtime_state='tier_validation') = 1 and (select count(*) from sc_approval_step s join sc_approval_policy p on p.id=s.policy_id where p.code='payment_request_approval' and s.approval_scope_key='finance_manager') >= 1 and (select count(*) from sc_approval_scope where scope_key='finance_manager') = 1 then 'ok' else 'S71 approval governance seed missing' end;" \
  "select p.id, p.code, p.target_model, p.runtime_state, s.name as step_name, s.approval_scope_key from sc_approval_policy p left join sc_approval_step s on s.policy_id=p.id where p.code='payment_request_approval';"
run_check "S71 scene governance audit records exist" "s71_governance_audit_surface" \
  "select case when (select count(*) from sc_scene_validation where status='pass' and scene_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_scene_067_demo_ops')) >= 1 and (select count(*) from sc_scene_audit_log where event in ('publish','update_pref') and scene_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_scene_067_demo_ops')) >= 2 and (select count(*) from sc_capability_audit_log where source_pack_id='s67.demo.surface.pack') >= 1 then 'ok' else 'S71 scene governance records missing' end;" \
  "select 'validation' as kind, id, status as value from sc_scene_validation where scene_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_scene_067_demo_ops') union all select 'scene_audit', id, event from sc_scene_audit_log where scene_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_scene_067_demo_ops') union all select 'capability_audit', id, event from sc_capability_audit_log where source_pack_id='s67.demo.surface.pack';"
run_check "S71 user preference and audit log exist" "s71_governance_audit_surface" \
  "select case when (select count(*) from sc_user_preference where user_id in (select res_id from ir_model_data where module='base' and name='user_admin') and default_scene_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_scene_067_demo_ops')) = 1 and (select count(*) from sc_audit_log where event_code='S71_PAYMENT_REQUEST_REVIEW' and trace_id='S71-GOV-AUDIT-001') = 1 then 'ok' else 'S71 preference audit records missing' end;" \
  "select 'preference' as kind, id, user_id, default_scene_id, null as event_code, null as trace_id from sc_user_preference where user_id in (select res_id from ir_model_data where module='base' and name='user_admin') union all select 'audit', id, actor_uid, project_id, event_code, trace_id from sc_audit_log where trace_id='S71-GOV-AUDIT-001';"
run_check "S72 project stage and next action rules exist" "s72_project_governance_surface" \
  "select case when (select count(*) from sc_project_stage_requirement_item where name like 'S72 %' and lifecycle_state='in_progress' and active is true) = 2 and (select count(*) from sc_project_next_action_rule where name like 'S72 %' and lifecycle_state='in_progress' and active is true) = 2 then 'ok' else 'S72 project governance rules missing' end;" \
  "select 'requirement' as kind, id, name, lifecycle_state, active from sc_project_stage_requirement_item where name like 'S72 %' union all select 'next_action', id, name, lifecycle_state, active from sc_project_next_action_rule where name like 'S72 %';"
run_check "S72 project member staging records exist" "s72_project_governance_surface" \
  "select case when (select count(*) from sc_project_member_staging where import_batch='s72_project_governance_surface' and role_fact_status in ('resolved','missing')) = 2 then 'ok' else 'S72 member staging records missing' end;" \
  "select id, legacy_member_id, project_id, user_id, legacy_role_text, role_fact_status, import_batch from sc_project_member_staging where import_batch='s72_project_governance_surface' order by id;"
run_check "S72 operating metrics project view has output" "s72_project_governance_surface" \
  "select case when (select count(*) from sc_operating_metrics_project where project_id in (select res_id from ir_model_data where module='smart_construction_demo' and name in ('sc_demo_project_001','sc_demo_project_069_payment_ledger'))) >= 1 then 'ok' else 'S72 operating metrics missing' end;" \
  "select project_id, receipt_amount, output_invoice_amount, input_invoice_amount, settlement_amount_total, settlement_amount_payable, receipt_count, invoice_count from sc_operating_metrics_project where project_id in (select res_id from ir_model_data where module='smart_construction_demo' and name in ('sc_demo_project_001','sc_demo_project_069_payment_ledger')) order by project_id;"
run_check "S73 project risk projection exists" "s73_risk_settlement_surface" \
  "select case when (select count(*) from project_risk where project_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_project_073_risk') and health_state='risk') = 1 then 'ok' else 'S73 project risk projection missing' end;" \
  "select id, project_id, name, health_state from project_risk where project_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_project_073_risk');"
run_check "S73 risk actions exist" "s73_risk_settlement_surface" \
  "select case when (select count(*) from project_risk_action where project_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_project_073_risk') and state in ('claimed','escalated')) = 2 then 'ok' else 'S73 risk actions missing' end;" \
  "select id, name, project_id, state, risk_level, owner_id from project_risk_action where project_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_project_073_risk') order by id;"
run_check "S73 compatible settlement records exist" "s73_risk_settlement_surface" \
  "select case when (select count(*) from project_settlement where name='S73-PSET-001' and state='confirmed' and amount=360000.0) = 1 and (select count(*) from project_settlement_line where settlement_id in (select id from project_settlement where name='S73-PSET-001')) = 2 then 'ok' else 'S73 compatible settlement missing' end;" \
  "select s.id, s.name, s.state, s.amount, count(l.id) as line_count from project_settlement s left join project_settlement_line l on l.settlement_id=s.id where s.name='S73-PSET-001' group by s.id, s.name, s.state, s.amount;"
run_check "S74 supplier type and partner records exist" "s74_partner_supplier_surface" \
  "select case when (select count(*) from sc_supplier_type where code in ('service','equipment') and active is true) = 2 and (select count(*) from res_partner where name='S74 四川智建咨询服务有限公司' and supplier_rank > 0 and customer_rank > 0 and sc_source_partner_code='S74-PARTNER-001') = 1 then 'ok' else 'S74 supplier partner records missing' end;" \
  "select p.id, p.name, p.supplier_rank, p.customer_rank, p.sc_supplier_type, p.sc_supplier_type_label, p.sc_region from res_partner p where p.name='S74 四川智建咨询服务有限公司';"
run_check "S74 partner import review records exist" "s74_partner_supplier_surface" \
  "select case when (select count(*) from sc_partner_import_review where import_batch='s74_partner_supplier_surface' and review_state='candidate') = 1 and (select count(*) from sc_partner_import_review where import_batch='s74_partner_supplier_surface' and review_state='resolved' and target_partner_id is not null) = 1 then 'ok' else 'S74 partner import reviews missing' end;" \
  "select id, partner_name, review_reason, review_state, suggested_supplier_rank, confirmed_supplier_rank, target_partner_id from sc_partner_import_review where import_batch='s74_partner_supplier_surface' order by id;"
run_check "S75 invoice and expense summaries have output" "s75_summary_projection_surface" \
  "select case when (select count(*) from sc_invoice_category_summary where manual_invoice_count > 0) >= 1 and (select count(*) from sc_expense_reimbursement_summary where manual_count > 0) >= 1 then 'ok' else 'S75 invoice/expense summaries missing' end;" \
  "select 'invoice' as kind, id, display_name, amount_total as amount, invoice_count as record_count from sc_invoice_category_summary where manual_invoice_count > 0 union all select 'expense', id, display_name, amount, claim_count from sc_expense_reimbursement_summary where manual_count > 0 order by kind, id limit 10;"
run_check "S75 salary and company operation summaries have output" "s75_summary_projection_surface" \
  "select case when (select count(*) from sc_salary_summary where manual_count > 0) >= 1 and (select count(*) from sc_company_operation_summary where source_line_count > 0) >= 1 then 'ok' else 'S75 salary/company summaries missing' end;" \
  "select 'salary' as kind, id, display_name, net_salary as amount, document_count as record_count from sc_salary_summary where manual_count > 0 union all select 'company', id, period_label, income_amount + expense_amount, source_line_count from sc_company_operation_summary where source_line_count > 0 order by kind, id limit 10;"
run_check "S76 workflow compatibility chain exists" "s76_workflow_compat_surface" \
  "select case when (select count(*) from sc_workflow_def where code='s76_payment_request_compat' and state='published') = 1 and (select count(*) from sc_workflow_node where workflow_def_id in (select id from sc_workflow_def where code='s76_payment_request_compat')) = 3 and (select count(*) from sc_workflow_instance where workflow_def_id in (select id from sc_workflow_def where code='s76_payment_request_compat') and state='running') = 1 then 'ok' else 'S76 workflow chain missing' end;" \
  "select d.id as def_id, d.code, d.state, i.id as instance_id, i.state as instance_state, n.code as current_node from sc_workflow_def d left join sc_workflow_instance i on i.workflow_def_id=d.id left join sc_workflow_node n on n.id=i.current_node_id where d.code='s76_payment_request_compat';"
run_check "S76 workflow workitem and logs exist" "s76_workflow_compat_surface" \
  "select case when (select count(*) from sc_workflow_workitem where instance_id in (select id from sc_workflow_instance where workflow_def_id in (select id from sc_workflow_def where code='s76_payment_request_compat')) and status='todo') = 1 and (select count(*) from sc_workflow_log where instance_id in (select id from sc_workflow_instance where workflow_def_id in (select id from sc_workflow_def where code='s76_payment_request_compat'))) = 2 then 'ok' else 'S76 workflow workitem/log missing' end;" \
  "select 'workitem' as kind, id, status as value from sc_workflow_workitem where instance_id in (select id from sc_workflow_instance where workflow_def_id in (select id from sc_workflow_def where code='s76_payment_request_compat')) union all select 'log', id, action from sc_workflow_log where instance_id in (select id from sc_workflow_instance where workflow_def_id in (select id from sc_workflow_def where code='s76_payment_request_compat')) order by kind, id;"
run_check "S80 material execution chain exists" "s80_execution_management_surface" \
  "select case when (select count(*) from sc_material_purchase_request where name='S80-MPR-001') = 1 and (select count(*) from sc_material_acceptance where name='S80-MA-001' and state='accepted') = 1 and (select count(*) from sc_material_inbound where name='S80-MIN-001' and state='received') = 1 and (select count(*) from sc_material_outbound where name='S80-MOUT-001' and state='issued') = 1 and (select count(*) from sc_material_settlement where name='S80-MSET-001' and state='confirmed') = 1 then 'ok' else 'S80 material chain missing' end;" \
  "select 'request' as kind, id, name, state from sc_material_purchase_request where name='S80-MPR-001' union all select 'acceptance', id, name, state from sc_material_acceptance where name='S80-MA-001' union all select 'inbound', id, name, state from sc_material_inbound where name='S80-MIN-001' union all select 'outbound', id, name, state from sc_material_outbound where name='S80-MOUT-001' union all select 'settlement', id, name, state from sc_material_settlement where name='S80-MSET-001';"
run_check "S80 plan quality safety records exist" "s80_execution_management_surface" \
  "select case when (select count(*) from sc_plan where name='S80 主体结构月度执行计划') = 1 and (select count(*) from sc_plan_report where name='S80 周计划进度汇报') = 1 and (select count(*) from sc_quality_issue where name='S80 钢筋保护层垫块局部缺失' and state='closed') = 1 and (select count(*) from sc_safety_issue where name='S80 楼层临边防护局部松动' and state='closed') = 1 then 'ok' else 'S80 plan/quality/safety missing' end;" \
  "select 'plan' as kind, id, name, state from sc_plan where name='S80 主体结构月度执行计划' union all select 'quality', id, name, state from sc_quality_issue where name='S80 钢筋保护层垫块局部缺失' union all select 'safety', id, name, state from sc_safety_issue where name='S80 楼层临边防护局部松动';"
run_check "S80 labor and equipment records exist" "s80_execution_management_surface" \
  "select case when (select count(*) from sc_labor_plan where name='S80-LP-001') = 1 and (select count(*) from sc_labor_request where name='S80-LR-001') = 1 and (select count(*) from sc_attendance_checkin where name='S80-ATT-001' and state='confirmed') = 1 and (select count(*) from sc_equipment_plan where name='S80-EP-001') = 1 and (select count(*) from sc_equipment_request where name='S80-ER-001') = 1 and (select count(*) from sc_equipment_usage where name='S80-EU-001' and state='confirmed') = 1 then 'ok' else 'S80 labor/equipment missing' end;" \
  "select 'labor_plan' as kind, id, name, state from sc_labor_plan where name='S80-LP-001' union all select 'labor_request', id, name, state from sc_labor_request where name='S80-LR-001' union all select 'attendance', id, name, state from sc_attendance_checkin where name='S80-ATT-001' union all select 'equipment_plan', id, name, state from sc_equipment_plan where name='S80-EP-001' union all select 'equipment_request', id, name, state from sc_equipment_request where name='S80-ER-001' union all select 'equipment_usage', id, name, state from sc_equipment_usage where name='S80-EU-001';"
run_check "S85 fund and financing records exist" "s85_admin_finance_surface" \
  "select case when (select count(*) from sc_fund_account where name='S85 项目监管户') = 1 and (select count(*) from sc_financing_loan where name='S85-FL-001' and state='confirmed') = 1 then 'ok' else 'S85 fund/financing missing' end;" \
  "select 'fund_account' as kind, id, name, state from sc_fund_account where name='S85 项目监管户' union all select 'financing_loan', id, name, state from sc_financing_loan where name='S85-FL-001';"
run_check "S85 admin and payroll records exist" "s85_admin_finance_surface" \
  "select case when (select count(*) from sc_document_admin_document where name in ('S85 安全生产许可证登记','S85 合同原件借阅申请') and state='done') = 2 and (select count(*) from sc_office_admin_document where name in ('S85 项目经理调休审批','S85 项目章使用审批') and state='done') = 2 and (select count(*) from sc_hr_payroll_document where name in ('S85 项目管理人员工资登记','S85 节点奖登记') and state='done') = 2 then 'ok' else 'S85 admin/payroll missing' end;" \
  "select 'document' as kind, id, name, state from sc_document_admin_document where name like 'S85 %' union all select 'office', id, name, state from sc_office_admin_document where name like 'S85 %' union all select 'payroll', id, name, state from sc_hr_payroll_document where name like 'S85 %';"
run_check "S85 subcontract chain exists" "s85_admin_finance_surface" \
  "select case when (select count(*) from sc_subcontract_plan where name='S85-SP-001' and state='approved') = 1 and (select count(*) from sc_subcontract_request where name='S85-SR-001' and state='approved') = 1 and (select count(*) from sc_subcontract_register where name='S85-SREG-001' and state='active') = 1 and (select count(*) from sc_subcontract_settlement where name='S85-SSET-001' and state='confirmed') = 1 and (select count(*) from sc_subcontract_price where name='S85-SPRICE-001' and state='active') = 1 then 'ok' else 'S85 subcontract chain missing' end;" \
  "select 'plan' as kind, id, name, state from sc_subcontract_plan where name='S85-SP-001' union all select 'request', id, name, state from sc_subcontract_request where name='S85-SR-001' union all select 'register', id, name, state from sc_subcontract_register where name='S85-SREG-001' union all select 'settlement', id, name, state from sc_subcontract_settlement where name='S85-SSET-001' union all select 'price', id, name, state from sc_subcontract_price where name='S85-SPRICE-001';"
run_check "S86 tender chain exists" "s86_tender_rental_finance_surface" \
  "select case when (select count(*) from tender_bid where name='S86-TB-001' and state='won') = 1 and (select count(*) from tender_bid_line where bid_id in (select id from tender_bid where name='S86-TB-001')) = 2 and (select count(*) from tender_doc_purchase where bid_id in (select id from tender_bid where name='S86-TB-001') and state='approved') = 1 and (select count(*) from tender_opening where bid_id in (select id from tender_bid where name='S86-TB-001') and result='won') = 1 and (select count(*) from tender_guarantee where bid_id in (select id from tender_bid where name='S86-TB-001') and state='confirmed') = 2 then 'ok' else 'S86 tender chain missing' end;" \
  "select id, name, tender_name, state, bid_amount from tender_bid where name='S86-TB-001';"
run_check "S86 fund deposit and adjustment records exist" "s86_tender_rental_finance_surface" \
  "select case when (select count(*) from sc_fund_account_operation where name in ('S86-FUND-TR-001','S86-FUND-DAY-001')) = 2 and (select count(*) from sc_expense_claim where name in ('S86-DEP-PAY-001','S86-DEP-REF-001') and state='done') = 2 and (select count(*) from sc_settlement_adjustment where name='S86-ADJ-001' and state='confirmed') = 1 then 'ok' else 'S86 fund/deposit/adjustment missing' end;" \
  "select 'fund_op' as kind, id, name, state from sc_fund_account_operation where name like 'S86-FUND-%' union all select 'deposit', id, name, state from sc_expense_claim where name like 'S86-DEP-%' union all select 'adjustment', id, name, state from sc_settlement_adjustment where name='S86-ADJ-001';"
run_check "S86 material rental chain exists" "s86_tender_rental_finance_surface" \
  "select case when (select count(*) from sc_material_rental_plan where name='S86-MRP-001' and state='approved') = 1 and (select count(*) from sc_material_rental_order where name='S86-MRO-001' and state='settled') = 1 and (select count(*) from sc_material_rental_settlement where name='S86-MRS-001' and state='paid') = 1 then 'ok' else 'S86 material rental chain missing' end;" \
  "select 'plan' as kind, id, name, state from sc_material_rental_plan where name='S86-MRP-001' union all select 'order', id, name, state from sc_material_rental_order where name='S86-MRO-001' union all select 'settlement', id, name, state from sc_material_rental_settlement where name='S86-MRS-001';"
run_check "S87 labor resource records exist" "s87_resource_contract_surface" \
  "select case when (select count(*) from sc_labor_usage where name='S87-LU-001' and state='confirmed') = 1 and (select count(*) from sc_labor_settlement where name='S87-LS-001' and state='confirmed') = 1 and (select count(*) from sc_labor_settlement_line where settlement_id in (select id from sc_labor_settlement where name='S87-LS-001')) = 1 and (select count(*) from sc_labor_price where name='S87-LPRICE-001' and state='active') = 1 then 'ok' else 'S87 labor resource records missing' end;" \
  "select 'usage' as kind, id, name, state from sc_labor_usage where name='S87-LU-001' union all select 'settlement', id, name, state from sc_labor_settlement where name='S87-LS-001' union all select 'price', id, name, state from sc_labor_price where name='S87-LPRICE-001';"
run_check "S87 equipment resource records exist" "s87_resource_contract_surface" \
  "select case when (select count(*) from sc_equipment_settlement where name='S87-ES-001' and state='confirmed') = 1 and (select count(*) from sc_equipment_settlement_line where settlement_id in (select id from sc_equipment_settlement where name='S87-ES-001')) = 1 and (select count(*) from sc_equipment_price where name='S87-EPRICE-001' and state='active') = 1 then 'ok' else 'S87 equipment resource records missing' end;" \
  "select 'settlement' as kind, id, name, state from sc_equipment_settlement where name='S87-ES-001' union all select 'price', id, name, state from sc_equipment_price where name='S87-EPRICE-001';"
run_check "S87 contract records exist" "s87_resource_contract_surface" \
  "select case when (select count(*) from sc_general_contract where name='S87-GC-001' and state='signed') = 1 and (select count(*) from sc_contract_event where event_no in ('S87-CE-001','S87-CE-002') and state in ('approved','done')) = 2 then 'ok' else 'S87 contract records missing' end;" \
  "select 'general_contract' as kind, id, name, state from sc_general_contract where name='S87-GC-001' union all select 'contract_event', id, name, state from sc_contract_event where event_no in ('S87-CE-001','S87-CE-002');"
run_check "S88 output invoice ledger record exists" "s88_output_invoice_surface" \
  "select case when (select count(*) from sc_invoice_registration where name='S88-OUT-INV-001' and direction='output' and state='registered') = 1 and (select count(*) from sc_output_invoice_ledger where invoice_no='S88-OUT-NO-001' and adjustment_kind='normal') = 1 then 'ok' else 'S88 output invoice ledger missing' end;" \
  "select id, invoice_no, adjustment_kind, invoice_amount, amount_no_tax, tax_amount from sc_output_invoice_ledger where invoice_no='S88-OUT-NO-001';"
run_check "S88 output invoice adjustment record exists" "s88_output_invoice_surface" \
  "select case when (select count(*) from sc_output_invoice_adjustment where name='S88-OIA-001' and state='draft' and invoice_no='S88-OUT-NO-001' and red_flush_invoice_amount < 0) = 1 then 'ok' else 'S88 output invoice adjustment missing' end;" \
  "select id, name, state, invoice_no, original_invoice_amount, red_flush_invoice_amount from sc_output_invoice_adjustment where name='S88-OIA-001';"
run_check "S89 quality standard and loop records exist" "s89_quality_safety_surface" \
  "select case when (select count(*) from sc_check_standard where name='S89 主体结构质量检查标准') = 1 and (select count(*) from sc_check_standard_item where name='钢筋保护层厚度') = 1 and (select count(*) from sc_quality_issue where name='S89 梁底钢筋保护层偏差' and state='closed') = 1 and (select count(*) from sc_quality_rectification where issue_id in (select id from sc_quality_issue where name='S89 梁底钢筋保护层偏差')) = 1 and (select count(*) from sc_quality_recheck where issue_id in (select id from sc_quality_issue where name='S89 梁底钢筋保护层偏差') and result='passed') = 1 then 'ok' else 'S89 quality records missing' end;" \
  "select 'issue' as kind, id, name, state from sc_quality_issue where name='S89 梁底钢筋保护层偏差' union all select 'standard', id, name, null as state from sc_check_standard where name='S89 主体结构质量检查标准';"
run_check "S89 safety plan risk and loop records exist" "s89_quality_safety_surface" \
  "select case when (select count(*) from sc_safety_plan where name='S89 高支模专项安全施工方案' and state='approved') = 1 and (select count(*) from sc_safety_disclosure where name='S89 高支模班前安全交底' and state='approved') = 1 and (select count(*) from sc_risk_library where name='S89 项目安全风险库') = 1 and (select count(*) from sc_risk_item where name='高支模架体失稳') = 1 and (select count(*) from sc_hazard_source where name='S89 1#楼高支模危险源' and state='controlled') = 1 and (select count(*) from sc_safety_issue where name='S89 高支模剪刀撑局部缺失' and state='closed') = 1 and (select count(*) from sc_safety_patrol_task where name='S89 高支模专项巡检' and state='done') = 1 then 'ok' else 'S89 safety records missing' end;" \
  "select 'plan' as kind, id, name, state from sc_safety_plan where name='S89 高支模专项安全施工方案' union all select 'hazard', id, name, state from sc_hazard_source where name='S89 1#楼高支模危险源' union all select 'issue', id, name, state from sc_safety_issue where name='S89 高支模剪刀撑局部缺失' union all select 'patrol', id, name, state from sc_safety_patrol_task where name='S89 高支模专项巡检';"
run_check "S89 site photo batches exist" "s89_quality_safety_surface" \
  "select case when count(*) = 2 then 'ok' else 'S89 photo batches missing' end from sc_site_photo_batch where name in ('S89 质量整改复验照片','S89 安全整改复验照片');" \
  "select id, name, evidence_stage, quality_issue_id, safety_issue_id from sc_site_photo_batch where name in ('S89 质量整改复验照片','S89 安全整改复验照片') order by name;"
run_check "S90 users exist" "s90_users_roles" \
  "select case when count(*) >= 6 then 'ok' else 'S90 users missing' end from res_users where login in ('demo_pm','demo_finance','demo_cost','demo_audit','demo_readonly','svc_e2e_smoke');" \
  "select id, login, active from res_users where login in ('demo_pm','demo_finance','demo_cost','demo_audit','demo_readonly','svc_e2e_smoke') order by login;"
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
