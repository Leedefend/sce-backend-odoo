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
const outDir = path.join(ARTIFACTS_DIR, 'business-handling-browser-matrix', ts);

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
        'X-Trace-Id': `business-browser-matrix-${Date.now()}`,
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

async function listOne(page, model, domain, fields) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'list',
    model,
    domain,
    fields,
    limit: 1,
    context: {},
  });
  const records = Array.isArray(resp.data?.records) ? resp.data.records : [];
  if (!records.length) throw new Error(`fixture missing: ${model} ${JSON.stringify(domain || [])}`);
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

function scenarioVals(scenario, fixtures, marker) {
  const base = {
    name: `${scenario.label} 浏览器矩阵验收 ${marker}`,
    fact_type: scenario.factType,
    business_date: '2026-05-02',
    project_id: Number(fixtures.project.id),
    partner_id: Number(fixtures.partner.id),
    department_id: Number(fixtures.department.id),
    handler_id: Number(fixtures.userId),
    description: `business_handling_browser_matrix ${marker}`,
  };
  if (fixtures.uom?.id) base.uom_id = Number(fixtures.uom.id);
  return { ...base, ...scenario.extraVals(fixtures, marker) };
}

const flowScenarios = [
  {
    key: 'labor_budget',
    label: '项目预算/人工预算',
    model: 'sc.project.budget.fact',
    factType: 'labor_budget',
    actionId: 797,
    menuId: 610,
    expectText: ['人工预算', '预算依据'],
    extraVals: (f) => ({
      cost_code_id: Number(f.costCode.id),
      budget_basis: '浏览器矩阵人工预算依据',
      original_budget_amount: 1000,
      adjusted_budget_amount: 1200,
      amount: 1200,
    }),
  },
  {
    key: 'archive_document',
    label: '施工资料/归档备案',
    model: 'sc.project.document.fact',
    factType: 'archive_document',
    actionId: 805,
    menuId: 619,
    expectText: ['归档备案', '档案编号'],
    extraVals: (_f, marker) => ({
      document_category: '竣工资料',
      document_version: 'V1',
      archive_no: `ARCH-BROWSER-${marker}`,
      owner_name: '浏览器验收责任人',
    }),
  },
  {
    key: 'attendance_record',
    label: '劳务管理/考勤记录',
    model: 'sc.labor.document',
    factType: 'attendance_record',
    actionId: 814,
    menuId: 631,
    expectText: ['考勤记录', '班组'],
    extraVals: () => ({
      labor_team: '浏览器验收班组',
      work_content: '现场作业',
      worker_count: 3,
      work_hours: 24,
      attendance_date: '2026-05-02',
      quantity: 3,
    }),
  },
  {
    key: 'equipment_usage',
    label: '机械设备/设备使用登记',
    model: 'sc.equipment.document',
    factType: 'equipment_usage',
    actionId: 819,
    menuId: 636,
    expectText: ['设备使用登记', '设备名称'],
    extraVals: (_f, marker) => ({
      equipment_name: '浏览器验收设备',
      equipment_code: `EQ-BROWSER-${marker}`,
      usage_location: '一标段',
      usage_hours: 8,
      operator_name: '浏览器验收操作员',
      quantity: 1,
    }),
  },
  {
    key: 'subcontract_register',
    label: '专业分包/分包登记',
    model: 'sc.subcontract.document',
    factType: 'subcontract_register',
    actionId: 824,
    menuId: 641,
    expectText: ['分包登记', '分包范围'],
    extraVals: (f) => ({
      subcontract_scope: '主体结构劳务',
      subcontractor_id: Number(f.partner.id),
      start_date: '2026-05-02',
      end_date: '2026-05-10',
    }),
  },
  {
    key: 'quality_rectification',
    label: '施工管理/质量整改',
    model: 'sc.construction.inspection',
    factType: 'quality_rectification',
    actionId: 828,
    menuId: 646,
    expectText: ['质量整改', '检查位置'],
    extraVals: (f) => ({
      inspection_location: '二层梁板',
      responsible_party_id: Number(f.partner.id),
      rectification_deadline: '2026-05-10',
      rectification_result: '复查合格',
    }),
  },
  {
    key: 'daily_report',
    label: '施工管理/日报表',
    model: 'sc.construction.report',
    factType: 'daily_report',
    actionId: 831,
    menuId: 650,
    expectText: ['日报表', '天气'],
    extraVals: () => ({
      period_start: '2026-05-02',
      period_end: '2026-05-02',
      weather: '晴',
      manpower_count: 12,
      completed_work: '完成钢筋绑扎',
      next_plan: '模板安装',
    }),
  },
  {
    key: 'fund_transfer_between',
    label: '资金账户/资金调拨',
    model: 'sc.fund.operation',
    factType: 'fund_transfer_between',
    actionId: 841,
    menuId: 669,
    expectText: ['资金调拨', '转出账户'],
    extraVals: () => ({
      operation_reason: '项目资金调拨',
      source_account: '公司基本户',
      target_account: '项目专户',
      amount: 5000,
    }),
  },
];

const writeScenarios = [
  {
    key: 'cost_ledger',
    label: '成本中心/成本台账',
    model: 'project.cost.ledger',
    actionId: 511,
    menuId: 372,
    expectText: ['成本台账', '金额'],
    vals: (f, marker) => ({
      project_id: Number(f.project.id),
      cost_code_id: Number(f.costCode.id),
      date: '2026-05-02',
      amount: 120,
      note: `business_handling_browser_matrix ${marker}`,
      source_model: 'business_handling_browser_matrix',
      source_id: marker % 1000000000,
    }),
  },
];

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
    checks: [],
    created: {},
    cleanup: {},
  };

  try {
    await login(page);
    const fixtures = {
      project: await listOne(page, 'project.project', [], ['id', 'name']),
      partner: await listOne(page, 'res.partner', [], ['id', 'name']),
      department: await listOne(page, 'hr.department', [], ['id', 'name']),
      costCode: await listOne(page, 'project.cost.code', [], ['id', 'name']),
      uom: await listOne(page, 'uom.uom', [], ['id', 'name']),
      userId: Number(await page.evaluate(() => JSON.parse(sessionStorage.getItem('sc_session') || '{}')?.user?.id || 0)) || 16,
    };

    for (const scenario of flowScenarios) {
      const check = { scenario: scenario.key, label: scenario.label, status: 'fail' };
      try {
        const createText = await openCreateForm(page, scenario);
        check.create_form_ok = true;
        check.create_form_text_hits = scenario.expectText.filter((text) => createText.includes(text));
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
        record = await readRecord(page, scenario.model, id, ['id', 'state', 'document_no']);
        check.final_record = record;
        check.status = check.create_form_ok && check.after_submit_state === 'in_progress' && record.state === 'done' && Boolean(record.document_no)
          ? 'pass'
          : 'fail';
        await page.screenshot({ path: path.join(outDir, `${scenario.key}.png`), fullPage: true });
      } catch (err) {
        check.error = err instanceof Error ? err.stack || err.message : String(err);
      }
      summary.checks.push(check);
    }

    for (const scenario of writeScenarios) {
      const check = { scenario: scenario.key, label: scenario.label, status: 'fail' };
      try {
        const createText = await openCreateForm(page, scenario);
        check.create_form_ok = true;
        check.create_form_text_hits = scenario.expectText.filter((text) => createText.includes(text));
        const id = await createRecord(page, scenario.model, scenario.vals(fixtures, marker), {});
        summary.created[scenario.key] = { model: scenario.model, ids: [id] };
        await openRecord(page, scenario, id);
        const record = await readRecord(page, scenario.model, id, ['id', 'amount', 'note']);
        check.final_record = record;
        check.status = check.create_form_ok && Number(record.amount) === 120 && normalize(record.note) === `business_handling_browser_matrix ${marker}`
          ? 'pass'
          : 'fail';
        await page.screenshot({ path: path.join(outDir, `${scenario.key}.png`), fullPage: true });
      } catch (err) {
        check.error = err instanceof Error ? err.stack || err.message : String(err);
      }
      summary.checks.push(check);
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
    && summary.checks.length === flowScenarios.length + writeScenarios.length
    && summary.checks.every((row) => row.status === 'pass')
    && (summary.console_errors || []).length === 0;
  writeJson('summary.json', summary);
  console.log(`[business_handling_browser_matrix_acceptance] artifacts=${outDir}`);
  console.log(JSON.stringify({
    pass: summary.pass,
    checks: summary.checks.map((row) => ({ scenario: row.scenario, status: row.status })),
    console_errors: (summary.console_errors || []).length,
    error: summary.error || null,
  }, null, 2));
  if (!summary.pass) process.exit(1);
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[business_handling_browser_matrix_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
