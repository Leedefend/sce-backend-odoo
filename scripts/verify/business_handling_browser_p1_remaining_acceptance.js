#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const requireBase = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? path.join(process.cwd(), 'frontend/apps/web/package.json')
  : path.join(process.cwd(), 'package.json');
const requireFromRoot = createRequire(requireBase);
const { chromium } = requireFromRoot('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5174';
const DB_NAME = process.env.DB_NAME || 'sc_prod_sim';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'business-handling-browser-p1-remaining', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function attachPageGuards(page) {
  page.__consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') page.__consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    page.__consoleErrors.push(err.message);
  });
  page.on('dialog', async (dialog) => {
    await dialog.accept();
  });
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 30000 });
}

async function token(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intentRequest(page, intent, params, options = {}) {
  const authToken = await token(page);
  return page.evaluate(async ({ dbName, authToken: bearer, intentName, payload, allowError }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: bearer ? `Bearer ${bearer}` : '',
        'X-Trace-Id': `business-browser-p1-remaining-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params: payload }),
    });
    const body = await response.json().catch(() => ({}));
    if (!allowError && (!response.ok || body.ok === false)) {
      throw new Error(body?.error?.message || body?.message || `${intentName} failed`);
    }
    return {
      status: response.status,
      ok: body.ok === true,
      data: body.data || {},
      error: body.error || {},
      meta: body.meta || {},
    };
  }, {
    dbName: DB_NAME,
    authToken,
    intentName: intent,
    payload: params,
    allowError: Boolean(options.allowError),
  });
}

async function listOne(page, model, domain, fields, options = {}) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'list',
    model,
    domain,
    fields,
    limit: 1,
    context: {},
  }, options);
  const records = Array.isArray(resp.data?.records) ? resp.data.records : [];
  if (!records.length) {
    if (options.optional) return null;
    throw new Error(`fixture missing: ${model} ${JSON.stringify(domain || [])}`);
  }
  return records[0];
}

async function createRecord(page, model, vals, context = {}) {
  const resp = await intentRequest(page, 'api.data', { op: 'create', model, vals, context });
  const id = Number(resp.data?.id || 0);
  if (!id) throw new Error(`create ${model} returned no id: ${JSON.stringify(resp)}`);
  return id;
}

async function readRecord(page, model, id, fields) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model,
    ids: [id],
    fields,
    context: {},
  });
  const rows = Array.isArray(resp.data?.records) ? resp.data.records : [];
  return rows[0] || {};
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
  const text = normalize(await page.locator('.template-layout-shell').textContent());
  if (text.includes('页面加载失败') || text.includes('页面渲染失败') || text.includes('System exception')) {
    throw new Error(`form render failed: ${text.slice(0, 300)}`);
  }
  return text;
}

async function openCreateForm(page, scenario) {
  await page.goto(`${FRONTEND_URL}/f/${scenario.model}/new?menu_id=${scenario.menuId}&action_id=${scenario.actionId}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  return waitForFormReady(page);
}

async function openRecord(page, scenario, id) {
  await page.goto(`${FRONTEND_URL}/r/${scenario.model}/${id}?menu_id=${scenario.menuId}&action_id=${scenario.actionId}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  return waitForFormReady(page);
}

async function clickNativeButton(page, label) {
  const button = page.locator('button.native-action-btn').filter({ hasText: new RegExp(`^${label}$`) }).first();
  await button.waitFor({ timeout: 15000 });
  await button.click();
  await page.waitForTimeout(900);
}

async function buildFixtures(page) {
  return {
    project: await listOne(page, 'project.project', [], ['id', 'name']),
    partner: await listOne(page, 'res.partner', [], ['id', 'name']),
    department: await listOne(page, 'hr.department', [], ['id', 'name']),
    costCode: await listOne(page, 'project.cost.code', [], ['id', 'name']),
    uom: await listOne(page, 'uom.uom', [], ['id', 'name']),
    userId: Number(await page.evaluate(() => JSON.parse(sessionStorage.getItem('sc_session') || '{}')?.user?.id || 0)) || 16,
    product: await listOne(page, 'product.product', [], ['id', 'name'], { optional: true, allowError: true }),
    warehouse: await listOne(page, 'stock.warehouse', [], ['id', 'name'], { optional: true, allowError: true }),
    location: await listOne(page, 'stock.location', [], ['id', 'name'], { optional: true, allowError: true }),
  };
}

function baseVals(scenario, fixtures, marker) {
  const vals = {
    name: `${scenario.label} P1浏览器验收 ${marker}`,
    fact_type: scenario.factType,
    business_date: '2026-05-02',
    planned_date: '2026-05-02',
    due_date: '2026-05-10',
    project_id: Number(fixtures.project.id),
    partner_id: Number(fixtures.partner.id),
    department_id: Number(fixtures.department.id),
    handler_id: Number(fixtures.userId),
    quantity: 2,
    uom_id: Number(fixtures.uom.id),
    unit_price: 50,
    amount: 100,
    description: `business_handling_browser_p1_remaining ${marker}`,
  };
  return vals;
}

function modelSpecificVals(scenario, fixtures, marker) {
  switch (scenario.model) {
    case 'sc.project.budget.fact':
      return {
        cost_code_id: Number(fixtures.costCode.id),
        budget_basis: `${scenario.label} 编制依据`,
        original_budget_amount: 1000,
        adjusted_budget_amount: 1200,
        amount: 1200,
      };
    case 'sc.material.document': {
      const vals = {
        material_spec: 'P1浏览器验收规格',
        supplier_quote: 100,
        quantity: 2,
        amount: 100,
      };
      if (fixtures.product?.id) vals.product_id = Number(fixtures.product.id);
      if (fixtures.warehouse?.id) vals.warehouse_id = Number(fixtures.warehouse.id);
      if (fixtures.location?.id) {
        vals.source_location_id = Number(fixtures.location.id);
        vals.dest_location_id = Number(fixtures.location.id);
      }
      return vals;
    }
    case 'sc.labor.document':
      return {
        labor_team: 'P1浏览器验收班组',
        work_content: `${scenario.label} 作业内容`,
        worker_count: 3,
        work_hours: 24,
        attendance_date: '2026-05-02',
        amount: 100,
      };
    case 'sc.equipment.document':
      return {
        equipment_name: 'P1浏览器验收设备',
        equipment_code: `EQ-P1-${marker}`,
        usage_location: 'P1验收区段',
        usage_hours: 8,
        operator_name: 'P1浏览器验收操作员',
        amount: 100,
      };
    case 'sc.subcontract.document':
      return {
        subcontract_scope: `${scenario.label} 分包范围`,
        subcontractor_id: Number(fixtures.partner.id),
        start_date: '2026-05-02',
        end_date: '2026-05-10',
        amount: 100,
      };
    case 'sc.construction.inspection':
      return {
        inspection_location: 'P1验收检查部位',
        responsible_party_id: Number(fixtures.partner.id),
        rectification_deadline: '2026-05-10',
        rectification_result: 'P1浏览器验收复查合格',
      };
    case 'sc.construction.report':
      return {
        period_start: '2026-05-02',
        period_end: '2026-05-02',
        weather: '晴',
        manpower_count: 12,
        completed_work: `${scenario.label} 完成工作`,
        next_plan: '下一步计划',
      };
    case 'sc.finance.expense.document':
      return {
        expense_category: `${scenario.label} 费用类别`,
        payee_id: Number(fixtures.partner.id),
        bank_account: 'P1-BROWSER-ACCOUNT',
        invoice_no: `INV-P1-${marker}`,
        repayment_due_date: '2026-05-10',
        amount: 100,
      };
    case 'sc.fund.operation':
      return {
        operation_reason: `${scenario.label} 操作原因`,
        source_account: 'P1验收转出账户',
        target_account: 'P1验收转入账户',
        before_balance: 1000,
        after_balance: scenario.factType === 'balance_adjustment' ? 1200 : 1000,
        amount: 100,
      };
    case 'sc.analysis.report.fact':
      return {
        report_period_start: '2026-05-01',
        report_period_end: '2026-05-31',
        metric_name: `${scenario.label} 指标`,
        metric_value: 100,
        metric_unit: '元',
      };
    default:
      return {};
  }
}

function scenarioVals(scenario, fixtures, marker) {
  return {
    ...baseVals(scenario, fixtures, marker),
    ...modelSpecificVals(scenario, fixtures, marker),
  };
}

const remainingFlowScenarios = [
  { key: 'material_budget', label: '项目预算/物资预算', model: 'sc.project.budget.fact', factType: 'material_budget', actionId: 796, menuId: 609 },
  { key: 'machine_budget', label: '项目预算/机械预算', model: 'sc.project.budget.fact', factType: 'machine_budget', actionId: 798, menuId: 611 },
  { key: 'subcontract_budget', label: '项目预算/分包预算', model: 'sc.project.budget.fact', factType: 'subcontract_budget', actionId: 799, menuId: 612 },
  { key: 'measure_budget', label: '项目预算/措施费', model: 'sc.project.budget.fact', factType: 'measure_budget', actionId: 800, menuId: 613 },
  { key: 'tax_budget', label: '项目预算/税费', model: 'sc.project.budget.fact', factType: 'tax_budget', actionId: 801, menuId: 614 },
  { key: 'purchase_request', label: '物资管理/采购申请', model: 'sc.material.document', factType: 'purchase_request', actionId: 806, menuId: 622 },
  { key: 'rfq', label: '物资管理/询比价', model: 'sc.material.document', factType: 'rfq', actionId: 807, menuId: 623 },
  { key: 'inbound', label: '物资管理/入库单', model: 'sc.material.document', factType: 'inbound', actionId: 808, menuId: 624 },
  { key: 'outbound', label: '物资管理/出库单', model: 'sc.material.document', factType: 'outbound', actionId: 809, menuId: 625 },
  { key: 'settlement', label: '物资管理/材料结算', model: 'sc.material.document', factType: 'settlement', actionId: 810, menuId: 626 },
  { key: 'labor_plan', label: '劳务管理/劳务计划', model: 'sc.labor.document', factType: 'labor_plan', actionId: 811, menuId: 628 },
  { key: 'labor_request', label: '劳务管理/劳务申请', model: 'sc.labor.document', factType: 'labor_request', actionId: 812, menuId: 629 },
  { key: 'labor_employment', label: '劳务管理/劳务用工', model: 'sc.labor.document', factType: 'labor_employment', actionId: 813, menuId: 630 },
  { key: 'labor_settlement', label: '劳务管理/劳务结算', model: 'sc.labor.document', factType: 'labor_settlement', actionId: 815, menuId: 632 },
  { key: 'labor_price_library', label: '劳务管理/劳务价格库', model: 'sc.labor.document', factType: 'labor_price_library', actionId: 816, menuId: 633 },
  { key: 'equipment_plan', label: '机械设备/设备计划', model: 'sc.equipment.document', factType: 'equipment_plan', actionId: 817, menuId: 634 },
  { key: 'equipment_request', label: '机械设备/设备申请', model: 'sc.equipment.document', factType: 'equipment_request', actionId: 818, menuId: 635 },
  { key: 'equipment_settlement', label: '机械设备/设备结算', model: 'sc.equipment.document', factType: 'equipment_settlement', actionId: 820, menuId: 637 },
  { key: 'equipment_price_library', label: '机械设备/设备价格库', model: 'sc.equipment.document', factType: 'equipment_price_library', actionId: 821, menuId: 638 },
  { key: 'subcontract_plan', label: '专业分包/分包计划', model: 'sc.subcontract.document', factType: 'subcontract_plan', actionId: 822, menuId: 639 },
  { key: 'subcontract_request', label: '专业分包/分包申请', model: 'sc.subcontract.document', factType: 'subcontract_request', actionId: 823, menuId: 640 },
  { key: 'subcontract_settlement', label: '专业分包/分包结算', model: 'sc.subcontract.document', factType: 'subcontract_settlement', actionId: 825, menuId: 642 },
  { key: 'subcontract_price_library', label: '专业分包/分包价格库', model: 'sc.subcontract.document', factType: 'subcontract_price_library', actionId: 826, menuId: 643 },
  { key: 'quality_check', label: '施工管理/质量检查', model: 'sc.construction.inspection', factType: 'quality_check', actionId: 827, menuId: 645 },
  { key: 'safety_check', label: '施工管理/安全检查', model: 'sc.construction.inspection', factType: 'safety_check', actionId: 829, menuId: 647 },
  { key: 'safety_rectification', label: '施工管理/安全整改', model: 'sc.construction.inspection', factType: 'safety_rectification', actionId: 830, menuId: 648 },
  { key: 'weekly_report', label: '施工管理/周报表', model: 'sc.construction.report', factType: 'weekly_report', actionId: 832, menuId: 651 },
  { key: 'monthly_report', label: '施工管理/月报表', model: 'sc.construction.report', factType: 'monthly_report', actionId: 833, menuId: 652 },
  { key: 'project_cost_statistics', label: '成本中心/成本汇总', model: 'sc.analysis.report.fact', factType: 'project_cost_statistics', actionId: 834, menuId: 373 },
  { key: 'project_profit_statistics', label: '成本中心/经营利润', model: 'sc.analysis.report.fact', factType: 'project_profit_statistics', actionId: 860, menuId: 374 },
  { key: 'funding_plan_summary', label: '资金计划/资金计划汇总', model: 'sc.fund.operation', factType: 'funding_plan_summary', actionId: 835, menuId: 662 },
  { key: 'advance_fund', label: '费用报销/备用金', model: 'sc.finance.expense.document', factType: 'advance_fund', actionId: 836, menuId: 663 },
  { key: 'repayment_form', label: '费用报销/还款单', model: 'sc.finance.expense.document', factType: 'repayment_form', actionId: 838, menuId: 665 },
  { key: 'project_expense_claim', label: '费用报销/项目费用报销单', model: 'sc.finance.expense.document', factType: 'project_expense_claim', actionId: 839, menuId: 666 },
  { key: 'fund_transfer_out', label: '资金账户/资金划拨', model: 'sc.fund.operation', factType: 'fund_transfer_out', actionId: 840, menuId: 668 },
  { key: 'balance_adjustment', label: '资金账户/余额调整', model: 'sc.fund.operation', factType: 'balance_adjustment', actionId: 842, menuId: 670 },
  { key: 'fund_daily_report', label: '资金账户/资金日报表', model: 'sc.fund.operation', factType: 'fund_daily_report', actionId: 859, menuId: 343 },
];

async function runScenario(page, scenario, fixtures, marker, summary) {
  const check = { scenario: scenario.key, label: scenario.label, model: scenario.model, status: 'fail' };
  try {
    const createText = await openCreateForm(page, scenario);
    check.create_form_ok = true;
    check.create_form_has_label = createText.includes(scenario.label.split('/').pop());
    const id = await createRecord(
      page,
      scenario.model,
      scenarioVals(scenario, fixtures, marker),
      { default_fact_type: scenario.factType, default_name: scenario.label },
    );
    summary.created[scenario.key] = { model: scenario.model, ids: [id] };
    await openRecord(page, scenario, id);
    await clickNativeButton(page, '提交');
    let record = await readRecord(page, scenario.model, id, ['id', 'state', 'document_no']);
    check.after_submit_state = record.state;
    await openRecord(page, scenario, id);
    await clickNativeButton(page, '完成');
    record = await readRecord(page, scenario.model, id, ['id', 'state', 'document_no', 'fact_type']);
    check.final_record = record;
    check.status = check.create_form_ok
      && check.after_submit_state === 'in_progress'
      && record.state === 'done'
      && record.fact_type === scenario.factType
      && Boolean(record.document_no)
      ? 'pass'
      : 'fail';
    await page.screenshot({ path: path.join(outDir, `${scenario.key}.png`), fullPage: true });
  } catch (err) {
    check.error = err instanceof Error ? err.stack || err.message : String(err);
  }
  summary.checks.push(check);
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 }, locale: 'zh-CN' });
  attachPageGuards(page);

  const marker = Date.now();
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    artifact_dir: outDir,
    marker,
    scope: 'P1_FLOW_PROOF remaining paths not covered by business_handling_browser_matrix_acceptance_v1',
    expected_count: remainingFlowScenarios.length,
    checks: [],
    created: {},
    cleanup: {},
  };

  try {
    await login(page);
    const fixtures = await buildFixtures(page);
    summary.fixture_ids = Object.fromEntries(
      Object.entries(fixtures).map(([key, value]) => [key, value && value.id ? Number(value.id) : null]),
    );
    for (const scenario of remainingFlowScenarios) {
      await runScenario(page, scenario, fixtures, marker, summary);
    }
    summary.console_errors = page.__consoleErrors || [];
  } catch (err) {
    summary.error = err instanceof Error ? err.stack || err.message : String(err);
    summary.console_errors = page.__consoleErrors || [];
  } finally {
    for (const [key, value] of Object.entries(summary.created)) {
      summary.cleanup[key] = {
        ok: true,
        mode: 'manual_odoo_shell_required',
        model: value.model,
        ids: value.ids,
      };
    }
    await browser.close().catch(() => {});
  }

  summary.pass = !summary.error
    && summary.checks.length === remainingFlowScenarios.length
    && summary.checks.every((row) => row.status === 'pass')
    && (summary.console_errors || []).length === 0;
  writeJson('summary.json', summary);
  console.log(`[business_handling_browser_p1_remaining_acceptance] artifacts=${outDir}`);
  console.log(JSON.stringify({
    pass: summary.pass,
    checked: summary.checks.length,
    failed: summary.checks.filter((row) => row.status !== 'pass').map((row) => ({
      scenario: row.scenario,
      label: row.label,
      error: row.error ? String(row.error).split('\n')[0] : null,
      final_record: row.final_record || null,
    })),
    console_errors: (summary.console_errors || []).length,
    error: summary.error || null,
  }, null, 2));
  if (!summary.pass) process.exit(1);
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[business_handling_browser_p1_remaining_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
