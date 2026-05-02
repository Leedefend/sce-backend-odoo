#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const MATRIX_PATH = 'artifacts/function-usability-proof/current/business_handling_maturity_matrix_final_current.json';
const OUTPUT_PATH = 'artifacts/function-usability-proof/current/business_handling_browser_p1_coverage_audit.json';

const EVIDENCE_SOURCES = [
  {
    id: 'business_handling_browser_acceptance_v1',
    summary: 'artifacts/business-handling-browser/20260501T235445/summary.json',
    scenarios: [
      {
        scenario: 'browser_submit_done_finance_borrowing_form',
        label: '费用报销/借款单',
        model: 'sc.finance.expense.document',
        action_id: 837,
        menu_id: 664,
      },
    ],
  },
  {
    id: 'business_handling_browser_matrix_acceptance_v1',
    summary: 'artifacts/business-handling-browser-matrix/20260502T000221/summary.json',
    scenarios: [
      { scenario: 'labor_budget', label: '项目预算/人工预算', model: 'sc.project.budget.fact', action_id: 797, menu_id: 610 },
      { scenario: 'attendance_record', label: '劳务管理/考勤记录', model: 'sc.labor.document', action_id: 814, menu_id: 631 },
      { scenario: 'equipment_usage', label: '机械设备/设备使用登记', model: 'sc.equipment.document', action_id: 819, menu_id: 636 },
      { scenario: 'subcontract_register', label: '专业分包/分包登记', model: 'sc.subcontract.document', action_id: 824, menu_id: 641 },
      { scenario: 'quality_rectification', label: '施工管理/质量整改', model: 'sc.construction.inspection', action_id: 828, menu_id: 646 },
      { scenario: 'daily_report', label: '施工管理/日报表', model: 'sc.construction.report', action_id: 831, menu_id: 650 },
      { scenario: 'fund_transfer_between', label: '资金账户/资金调拨', model: 'sc.fund.operation', action_id: 841, menu_id: 669 },
      { scenario: 'cost_ledger', label: '成本中心/成本台账', model: 'project.cost.ledger', action_id: 511, menu_id: 372 },
    ],
  },
  {
    id: 'business_data_entry_browser_acceptance_v1',
    summary: 'artifacts/business-data-entry-browser/20260502T001857/summary.json',
    scenarios: [
      { scenario: 'tender_opening', label: '投标管理/开标记录', model: 'tender.opening', action_id: 650, menu_id: 454 },
      { scenario: 'tender_guarantee', label: '投标管理/投标保证金', model: 'tender.guarantee', action_id: 652, menu_id: 456 },
      { scenario: 'project_boq_line', label: '项目预算/预算清单', model: 'project.boq.line', action_id: 522, menu_id: 356 },
      { scenario: 'project_budget', label: '成本中心/目标成本', model: 'project.budget', action_id: 507, menu_id: 368 },
      { scenario: 'project_budget_cost_alloc', label: '成本中心/预算清单分摊', model: 'project.budget.cost.alloc', action_id: 513, menu_id: 369 },
    ],
  },
  {
    id: 'business_handling_browser_p1_remaining_acceptance_v1',
    summary: 'artifacts/business-handling-browser-p1-remaining/20260502T002749/summary.json',
    scenarios: [
      { scenario: 'material_budget', label: '项目预算/物资预算', model: 'sc.project.budget.fact', action_id: 796, menu_id: 609 },
      { scenario: 'machine_budget', label: '项目预算/机械预算', model: 'sc.project.budget.fact', action_id: 798, menu_id: 611 },
      { scenario: 'subcontract_budget', label: '项目预算/分包预算', model: 'sc.project.budget.fact', action_id: 799, menu_id: 612 },
      { scenario: 'measure_budget', label: '项目预算/措施费', model: 'sc.project.budget.fact', action_id: 800, menu_id: 613 },
      { scenario: 'tax_budget', label: '项目预算/税费', model: 'sc.project.budget.fact', action_id: 801, menu_id: 614 },
      { scenario: 'purchase_request', label: '物资管理/采购申请', model: 'sc.material.document', action_id: 806, menu_id: 622 },
      { scenario: 'rfq', label: '物资管理/询比价', model: 'sc.material.document', action_id: 807, menu_id: 623 },
      { scenario: 'inbound', label: '物资管理/入库单', model: 'sc.material.document', action_id: 808, menu_id: 624 },
      { scenario: 'outbound', label: '物资管理/出库单', model: 'sc.material.document', action_id: 809, menu_id: 625 },
      { scenario: 'settlement', label: '物资管理/材料结算', model: 'sc.material.document', action_id: 810, menu_id: 626 },
      { scenario: 'labor_plan', label: '劳务管理/劳务计划', model: 'sc.labor.document', action_id: 811, menu_id: 628 },
      { scenario: 'labor_request', label: '劳务管理/劳务申请', model: 'sc.labor.document', action_id: 812, menu_id: 629 },
      { scenario: 'labor_employment', label: '劳务管理/劳务用工', model: 'sc.labor.document', action_id: 813, menu_id: 630 },
      { scenario: 'labor_settlement', label: '劳务管理/劳务结算', model: 'sc.labor.document', action_id: 815, menu_id: 632 },
      { scenario: 'labor_price_library', label: '劳务管理/劳务价格库', model: 'sc.labor.document', action_id: 816, menu_id: 633 },
      { scenario: 'equipment_plan', label: '机械设备/设备计划', model: 'sc.equipment.document', action_id: 817, menu_id: 634 },
      { scenario: 'equipment_request', label: '机械设备/设备申请', model: 'sc.equipment.document', action_id: 818, menu_id: 635 },
      { scenario: 'equipment_settlement', label: '机械设备/设备结算', model: 'sc.equipment.document', action_id: 820, menu_id: 637 },
      { scenario: 'equipment_price_library', label: '机械设备/设备价格库', model: 'sc.equipment.document', action_id: 821, menu_id: 638 },
      { scenario: 'subcontract_plan', label: '专业分包/分包计划', model: 'sc.subcontract.document', action_id: 822, menu_id: 639 },
      { scenario: 'subcontract_request', label: '专业分包/分包申请', model: 'sc.subcontract.document', action_id: 823, menu_id: 640 },
      { scenario: 'subcontract_settlement', label: '专业分包/分包结算', model: 'sc.subcontract.document', action_id: 825, menu_id: 642 },
      { scenario: 'subcontract_price_library', label: '专业分包/分包价格库', model: 'sc.subcontract.document', action_id: 826, menu_id: 643 },
      { scenario: 'quality_check', label: '施工管理/质量检查', model: 'sc.construction.inspection', action_id: 827, menu_id: 645 },
      { scenario: 'safety_check', label: '施工管理/安全检查', model: 'sc.construction.inspection', action_id: 829, menu_id: 647 },
      { scenario: 'safety_rectification', label: '施工管理/安全整改', model: 'sc.construction.inspection', action_id: 830, menu_id: 648 },
      { scenario: 'weekly_report', label: '施工管理/周报表', model: 'sc.construction.report', action_id: 832, menu_id: 651 },
      { scenario: 'monthly_report', label: '施工管理/月报表', model: 'sc.construction.report', action_id: 833, menu_id: 652 },
      { scenario: 'project_cost_statistics', label: '成本中心/成本汇总', model: 'sc.analysis.report.fact', action_id: 834, menu_id: 373 },
      { scenario: 'project_profit_statistics', label: '成本中心/经营利润', model: 'sc.analysis.report.fact', action_id: 860, menu_id: 374 },
      { scenario: 'funding_plan_summary', label: '资金计划/资金计划汇总', model: 'sc.fund.operation', action_id: 835, menu_id: 662 },
      { scenario: 'advance_fund', label: '费用报销/备用金', model: 'sc.finance.expense.document', action_id: 836, menu_id: 663 },
      { scenario: 'repayment_form', label: '费用报销/还款单', model: 'sc.finance.expense.document', action_id: 838, menu_id: 665 },
      { scenario: 'project_expense_claim', label: '费用报销/项目费用报销单', model: 'sc.finance.expense.document', action_id: 839, menu_id: 666 },
      { scenario: 'fund_transfer_out', label: '资金账户/资金划拨', model: 'sc.fund.operation', action_id: 840, menu_id: 668 },
      { scenario: 'balance_adjustment', label: '资金账户/余额调整', model: 'sc.fund.operation', action_id: 842, menu_id: 670 },
      { scenario: 'fund_daily_report', label: '资金账户/资金日报表', model: 'sc.fund.operation', action_id: 859, menu_id: 343 },
    ],
  },
];

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function keyOf(row) {
  return `${row.model}|${Number(row.action_id)}|${Number(row.menu_id)}`;
}

function suffixMatch(pathValue, labelValue) {
  const pathParts = String(pathValue || '').split('/');
  const labelParts = String(labelValue || '').split('/');
  return labelParts.every((part) => pathParts.includes(part));
}

function buildEvidenceIndex() {
  const index = new Map();
  const sourceResults = [];
  for (const source of EVIDENCE_SOURCES) {
    const summary = readJson(source.summary);
    const checks = new Map((summary.checks || []).map((row) => [row.scenario, row]));
    const sourceResult = {
      id: source.id,
      summary: source.summary,
      pass: summary.pass === true,
      console_errors: (summary.console_errors || []).length,
      scenario_count: source.scenarios.length,
      failed_scenarios: [],
    };
    for (const scenario of source.scenarios) {
      const check = checks.get(scenario.scenario);
      const scenarioPass = sourceResult.pass
        && sourceResult.console_errors === 0
        && check
        && check.status === 'pass';
      if (!scenarioPass) {
        sourceResult.failed_scenarios.push({
          scenario: scenario.scenario,
          found: Boolean(check),
          status: check && check.status,
        });
      }
      index.set(keyOf(scenario), {
        source_id: source.id,
        summary: source.summary,
        scenario: scenario.scenario,
        label: scenario.label,
        scenario_pass: Boolean(scenarioPass),
      });
    }
    sourceResults.push(sourceResult);
  }
  return { index, sourceResults };
}

function main() {
  const matrix = readJson(MATRIX_PATH);
  const focusRows = (matrix.focus_rows || []).filter((row) => (
    row.priority === 'P1_FLOW_PROOF' || row.priority === 'P1_WRITE_PROOF'
  ));
  const { index, sourceResults } = buildEvidenceIndex();
  const rows = focusRows.map((row) => {
    const evidence = index.get(keyOf(row));
    const covered = Boolean(evidence && evidence.scenario_pass && suffixMatch(row.path, evidence.label));
    return {
      path: row.path,
      priority: row.priority,
      model: row.model,
      action_id: row.action_id,
      menu_id: row.menu_id,
      covered,
      evidence: evidence || null,
      reason: covered
        ? 'browser_evidence_pass'
        : evidence
          ? 'evidence_present_but_not_matching_or_failed'
          : 'missing_browser_evidence',
    };
  });
  const missing = rows.filter((row) => !row.covered);
  const result = {
    ok: missing.length === 0 && sourceResults.every((source) => source.pass && source.console_errors === 0 && !source.failed_scenarios.length),
    matrix: MATRIX_PATH,
    checked: rows.length,
    covered_count: rows.filter((row) => row.covered).length,
    missing_count: missing.length,
    priority_counts: {
      P1_FLOW_PROOF: rows.filter((row) => row.priority === 'P1_FLOW_PROOF').length,
      P1_WRITE_PROOF: rows.filter((row) => row.priority === 'P1_WRITE_PROOF').length,
    },
    evidence_sources: sourceResults,
    missing,
    rows,
  };
  fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(result, null, 2), 'utf8');
  console.log(JSON.stringify({
    ok: result.ok,
    checked: result.checked,
    covered_count: result.covered_count,
    missing_count: result.missing_count,
    output: OUTPUT_PATH,
  }, null, 2));
  if (!result.ok) process.exit(1);
}

main();
