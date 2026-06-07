#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

function loadPlaywright() {
  const candidates = [
    path.join(process.cwd(), 'frontend/apps/web/package.json'),
    path.join(process.cwd(), 'package.json'),
    '/tmp/sc-pw/package.json',
  ];
  for (const candidate of candidates) {
    if (!fs.existsSync(candidate)) continue;
    try {
      return createRequire(candidate)('playwright');
    } catch (_err) {
      // Try the next candidate.
    }
  }
  return require('playwright');
}

const { chromium } = loadPlaywright();

const FRONTEND_URL = (process.env.FRONTEND_URL || 'http://1.95.85.92:18081').replace(/\/$/, '');
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const BASELINE = process.env.BASELINE || 'scripts/verify/baselines/user_confirmed_formal_menu_policy_62.json';
const PRODUCT_KEY = process.env.PRODUCT_KEY || 'construction.standard';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts/verify';
const MAX_MENUS = Number(process.env.MAX_MENUS || 0);

const EXPECTED_TOTAL_BY_MENU_XMLID = {
  'smart_construction_core.menu_project_material_plan': 686,
  'smart_construction_core.menu_sc_material_quote_acceptance': 126,
  'smart_construction_core.menu_sc_material_inbound': 13184,
  'smart_construction_core.menu_sc_labor_usage_acceptance': 252,
  'smart_construction_core.menu_sc_labor_casual_acceptance': 8794,
  'smart_construction_core.menu_sc_subcontract_request_acceptance': 721,
  'smart_construction_core.menu_sc_equipment_shift_acceptance': 17502,
  'smart_construction_core.menu_sc_material_rental_in_acceptance': 166,
  'smart_construction_core.menu_sc_material_rental_return_acceptance': 37,
  'smart_construction_core.menu_sc_salary_registration': 233,
  'smart_construction_core.menu_sc_legacy_fuel_card_fact_acceptance': 8,
  'smart_construction_core.menu_sc_legacy_fuel_card_recharge_fact_acceptance': 32,
  'smart_construction_core.menu_sc_construction_diary': 3233,
  'smart_construction_core.menu_sc_expense_contract_execution': 1566,
};

const EXPECTED_VISIBLE_LABELS_BY_MENU_XMLID = {
  'smart_construction_core.menu_sc_settlement_order_income': [
    '结算单号',
    '标题',
    '项目',
    '结算金额',
    '送审金额',
    '审定金额',
  ],
  'smart_construction_core.menu_sc_settlement_order_expense': [
    '结算单号',
    '标题',
    '项目',
    '结算金额',
    '送审金额',
    '审定金额',
  ],
  'smart_construction_core.menu_ui_menu_config_policy_business_config': [
    '显示名称',
    '默认名称',
    '当前父级',
    '级别',
    '顺序',
    '移动到上级',
  ],
};

const REQUIRED_NONEMPTY_FIELDS_BY_MENU_XMLID = {
  'smart_construction_core.menu_sc_settlement_order_income': [
    'name',
    'title',
    'project_id',
    'settlement_amount',
    'submitted_amount',
    'approved_amount',
  ],
  'smart_construction_core.menu_sc_settlement_order_expense': [
    'name',
    'title',
    'project_id',
    'settlement_amount',
    'submitted_amount',
    'approved_amount',
  ],
};

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'user-confirmed-formal-menu-full-browser', ts);

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function loadMenus() {
  const payload = JSON.parse(fs.readFileSync(BASELINE, 'utf8'));
  const product = (payload.products || []).find((item) => item.product_key === PRODUCT_KEY) || (payload.products || [])[0];
  const rows = [];
  for (const group of product.menu_groups || []) {
    for (const menu of group.menus || []) {
      rows.push({
        group: group.group_label || group.label || '',
        label: menu.label || menu.name || '',
        menuXmlid: menu.menu_xmlid || menu.menu_key || '',
        actionId: Number(menu.action_id || 0),
        menuId: Number(menu.menu_id || 0),
        model: menu.res_model || '',
        route: menu.route || '',
      });
    }
  }
  return MAX_MENUS > 0 ? rows.slice(0, MAX_MENUS) : rows;
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  if (await inputs.nth(2).isEnabled().catch(() => false)) {
    await inputs.nth(2).fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 });
}

async function authToken(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intentRequest(page, intent, params) {
  const token = await authToken(page);
  const response = await page.evaluate(async ({ dbName, bearer, intentName, payload }) => {
    const resp = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Odoo-DB': dbName,
        Authorization: bearer ? `Bearer ${bearer}` : '',
        'X-Trace-Id': `formal-full-browser-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params: { db: dbName, ...payload } }),
    });
    const body = await resp.json().catch(() => ({}));
    return { status: resp.status, body };
  }, { dbName: DB_NAME, bearer: token, intentName: intent, payload: params });
  if (response.body?.ok !== true) {
    throw new Error(`${intent} failed: ${JSON.stringify(response.body?.error || response.body).slice(0, 800)}`);
  }
  return response.body.data || {};
}

function walkContainers(containers, out = []) {
  for (const container of Array.isArray(containers) ? containers : []) {
    if (Array.isArray(container.widgetList)) out.push(...container.widgetList);
    walkContainers(container.children, out);
  }
  return out;
}

function v2Widgets(contract) {
  return walkContainers(contract?.layoutContract?.containerTree || [])
    .filter((widget) => normalize(widget.fieldCode) && normalize(widget.label));
}

function v2DataParams(contract) {
  const primary = contract?.dataContract?.dataSource?.primary || {};
  const params = primary.params || {};
  const source = contract?.dataContract?.dataMeta?.sourceContext || {};
  return {
    model: primary.model || contract?.pageInfo?.model || '',
    fields: Array.isArray(params.fields) ? params.fields : ['id'],
    domain: Array.isArray(source.domain) ? source.domain : [],
    context_raw: normalize(source.context_raw),
    order: normalize(source.order),
  };
}

function hasBusinessValue(value) {
  if (value === null || value === undefined || value === false) return false;
  if (Array.isArray(value)) return value.some((item) => hasBusinessValue(item));
  if (typeof value === 'number') return Number.isFinite(value);
  const text = normalize(value);
  return Boolean(text && text !== '-' && text !== '--' && text !== '无' && text !== '空');
}

function recordHasAnyValue(records, fieldName) {
  return (Array.isArray(records) ? records : []).some((record) => hasBusinessValue(record?.[fieldName]));
}

function visibleBusinessValueFieldCount(records, widgets) {
  const fieldCodes = widgets
    .map((widget) => normalize(widget.fieldCode))
    .filter(Boolean)
    .slice(0, 12);
  let count = 0;
  for (const fieldCode of fieldCodes) {
    if (recordHasAnyValue(records, fieldCode)) count += 1;
  }
  return count;
}

async function openMenu(page, menu, expectedLabels, options = {}) {
  const url = `${FRONTEND_URL}/a/${menu.actionId}?menu_id=${menu.menuId}`;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    return !text.includes('正在加载页面') && !text.includes('Loading');
  }, null, { timeout: 45000 });
  if (options.allowEmpty) {
    await page.waitForFunction(() => {
      const text = String(document.body?.textContent || '');
      if (text.includes('当前视图使用可读降级渲染')) return false;
      return text.includes('当前还没有数据') || text.includes('共 0 条');
    }, null, { timeout: 45000 });
    return normalize(await page.locator('body').textContent());
  }
  await page.waitForFunction((payload) => {
    const text = String(document.body?.textContent || '');
    if (text.includes('当前视图使用可读降级渲染')) return false;
    return payload.labels.slice(0, Math.min(3, payload.labels.length)).every((label) => text.includes(label));
  }, { labels: expectedLabels }, { timeout: 45000 });
  return normalize(await page.locator('body').textContent());
}

async function verifyMenu(page, menu) {
  const errors = [];
  const contract = await intentRequest(page, 'ui.contract.v2', {
    op: 'action_open',
    action_id: menu.actionId,
    client_type: 'web_pc',
    delivery_profile: 'full',
  });
  const widgets = v2Widgets(contract);
  const labels = widgets.map((widget) => normalize(widget.label));
  const visibleLabels = EXPECTED_VISIBLE_LABELS_BY_MENU_XMLID[menu.menuXmlid] || labels;
  const dataParams = v2DataParams(contract);
  if (!dataParams.model) errors.push('missing_model');
  if (!widgets.length) errors.push('missing_list_widgets');
  if (menu.model && dataParams.model && menu.model !== dataParams.model) {
    errors.push(`model_mismatch:${menu.model}->${dataParams.model}`);
  }

  let data = null;
  if (dataParams.model && dataParams.fields.length) {
    data = await intentRequest(page, 'api.data', {
      op: 'list',
      model: dataParams.model,
      fields: dataParams.fields,
      domain: dataParams.domain,
      context_raw: dataParams.context_raw,
      order: dataParams.order,
      limit: 20,
      offset: 0,
      need_total: true,
    });
  }
  const total = Number(data?.total || 0);
  if (widgets.length <= 1 && total > 0) errors.push(`insufficient_visible_columns:${widgets.length}`);
  const records = Array.isArray(data?.records) ? data.records : [];
  const requiredNonemptyFields = REQUIRED_NONEMPTY_FIELDS_BY_MENU_XMLID[menu.menuXmlid] || [];
  for (const fieldName of requiredNonemptyFields) {
    if (!recordHasAnyValue(records, fieldName)) errors.push(`missing_sample_value:${fieldName}`);
  }
  if (total > 0 && visibleBusinessValueFieldCount(records, widgets) < 2) {
    errors.push('insufficient_visible_business_values');
  }
  const expectedTotal = EXPECTED_TOTAL_BY_MENU_XMLID[menu.menuXmlid];
  if (expectedTotal !== undefined && total !== expectedTotal) {
    errors.push(`total_mismatch:${expectedTotal}->${total}`);
  }

  let text = '';
  try {
    text = await openMenu(page, menu, visibleLabels, { allowEmpty: total === 0 });
  } catch (err) {
    errors.push(`browser_open_failed:${err.message}`);
    text = normalize(await page.locator('body').textContent().catch(() => ''));
  }
  if (text.includes('当前视图使用可读降级渲染')) errors.push('browser_degraded');
  if (!(total === 0 && (text.includes('当前还没有数据') || text.includes('共 0 条')))) {
    for (const label of visibleLabels.slice(0, Math.min(6, visibleLabels.length))) {
      if (!text.includes(label)) errors.push(`missing_visible_label:${label}`);
    }
  }
  return {
    ...menu,
    status: errors.length ? 'FAIL' : 'PASS',
    errors,
    pageName: contract?.pageInfo?.pageName || '',
    viewType: contract?.pageInfo?.viewType || '',
    model: dataParams.model,
    widgetCount: widgets.length,
    labels,
    total,
    expectedTotal,
    sampleCount: records.length,
    textExcerpt: text.slice(0, 500),
  };
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const executablePath = process.env.PLAYWRIGHT_EXECUTABLE_PATH || process.env.CHROMIUM_PATH || '';
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: 'zh-CN' });
  const menus = loadMenus();
  const results = [];
  try {
    await login(page);
    for (const menu of menus) {
      let result;
      try {
        result = await verifyMenu(page, menu);
      } catch (err) {
        result = {
          ...menu,
          status: 'FAIL',
          errors: [`menu_verify_failed:${err.message}`],
          widgetCount: 0,
          labels: [],
          total: 0,
          sampleCount: 0,
          textExcerpt: normalize(await page.locator('body').textContent().catch(() => '')).slice(0, 500),
        };
      }
      results.push(result);
      console.log(`${result.status} ${result.group}/${result.label} action=${result.actionId} total=${result.total}${result.errors.length ? ` errors=${result.errors.join('|')}` : ''}`);
    }
  } finally {
    await browser.close();
  }
  const payload = {
    status: results.every((row) => row.status === 'PASS') ? 'PASS' : 'FAIL',
    base_url: FRONTEND_URL,
    db: DB_NAME,
    login: LOGIN,
    product_key: PRODUCT_KEY,
    menu_count: results.length,
    fail_count: results.filter((row) => row.status !== 'PASS').length,
    artifact_dir: outDir,
    results,
  };
  writeJson('summary.json', payload);
  if (payload.status !== 'PASS') {
    console.error(`[user_confirmed_formal_menu_full_browser_alignment] FAIL artifacts=${outDir}`);
    process.exit(1);
  }
  console.log(`[user_confirmed_formal_menu_full_browser_alignment] PASS artifacts=${outDir}`);
}

main().catch((err) => {
  console.error(`[user_confirmed_formal_menu_full_browser_alignment] FAIL: ${err.message}`);
  process.exit(1);
});
