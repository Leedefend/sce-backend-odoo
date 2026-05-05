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

const DEFAULT_SPECIMENS = [
  { tier: 'M2', model: 'payment.request', recordId: 28489, actionId: 585, menuId: 0, label: '付款/收款申请' },
  { tier: 'M3', model: 'purchase.order', recordId: 9, actionId: 549, menuId: 0, label: '采购单' },
  { tier: 'M4', model: 'sc.legacy.receipt.income.fact', recordId: 7220, actionId: 561, menuId: 0, label: '历史收款收入事实' },
  { tier: 'M5', model: 'sc.dictionary', recordId: 5, actionId: 619, menuId: 0, label: '业务字典' },
];

const SPECIMENS = process.env.SPECIMENS_JSON
  ? JSON.parse(process.env.SPECIMENS_JSON)
  : DEFAULT_SPECIMENS;

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-model-tier', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function attachConsoleCapture(page) {
  page.__consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') page.__consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    page.__consoleErrors.push(err.message);
  });
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 });
}

async function token(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intentRequest(page, intent, params) {
  const authToken = await token(page);
  return page.evaluate(async ({ dbName, authToken: bearer, intentName, payload }) => {
    const headers = { 'Content-Type': 'application/json', 'X-Trace-Id': `form-model-tier-${Date.now()}` };
    if (bearer) headers.Authorization = `Bearer ${bearer}`;
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ intent: intentName, params: payload }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || body.ok === false) {
      const message = body?.error?.message || body?.message || `intent ${intentName} failed`;
      throw new Error(message);
    }
    return body.data || body;
  }, { dbName: DB_NAME, authToken, intentName: intent, payload: params });
}

async function openForm(page, specimen) {
  const query = new URLSearchParams();
  if (Number(specimen.menuId || 0) > 0) query.set('menu_id', String(specimen.menuId));
  if (Number(specimen.actionId || 0) > 0) query.set('action_id', String(specimen.actionId));
  await page.goto(
    `${FRONTEND_URL}/r/${encodeURIComponent(specimen.model)}/${specimen.recordId}?${query.toString()}`,
    { waitUntil: 'domcontentloaded', timeout: 45000 },
  );
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const shell = document.querySelector('.template-layout-shell');
    const text = String(shell?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

function contractSummary(contract) {
  const form = contract?.views?.form || {};
  const layout = Array.isArray(form.layout) ? form.layout : [];
  const fields = contract?.fields && typeof contract.fields === 'object' ? contract.fields : {};
  const fieldNames = Object.keys(fields);
  const subviews = form.subviews && typeof form.subviews === 'object' ? form.subviews : {};
  return {
    model: contract?.head?.model || contract?.model || '',
    form_present: Boolean(form && typeof form === 'object'),
    field_count: fieldNames.length,
    layout_nodes: layout.length,
    has_statusbar: Boolean(form.statusbar),
    header_buttons: Array.isArray(form.header_buttons) ? form.header_buttons.length : 0,
    smart_buttons: Array.isArray(form.button_box) ? form.button_box.length : 0,
    subview_count: Object.keys(subviews).length,
    chatter_enabled: Boolean(form.chatter?.enabled),
    attachments_enabled: Boolean(form.attachments?.enabled),
    rights: contract?.permissions?.effective?.rights || {},
  };
}

function hasReadonlyProjectionSurface(specimen, contractInfo, domInfo) {
  const rights = contractInfo.rights || {};
  return rights.read === true
    && rights.create !== true
    && rights.write !== true
    && contractInfo.field_count > 0
    && domInfo.visible_error === ''
    && domInfo.text_sample.length > 80
    && domInfo.text_sample.includes(String(specimen.label || '').trim());
}

async function domSummary(page) {
  return page.evaluate(() => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const shell = document.querySelector('.template-layout-shell');
    return {
      title: clean(document.querySelector('.template-page-title, h1, .title')?.textContent || ''),
      input_count: document.querySelectorAll('.template-layout-shell input, .template-layout-shell textarea, .template-layout-shell select').length,
      field_count: document.querySelectorAll('.template-layout-shell .field').length,
      readonly_count: document.querySelectorAll('.readonly-value, .readonly-field, .form-readonly, .native-readonly').length,
      tabs: Array.from(document.querySelectorAll('button.native-tab')).map((node) => clean(node.textContent)).filter(Boolean),
      statusbar_count: document.querySelectorAll('.native-statusbar-step').length,
      smart_button_count: document.querySelectorAll('button.native-action-btn--smart').length,
      body_action_count: document.querySelectorAll('button.native-action-btn:not(.native-action-btn--smart)').length,
      o2m_count: document.querySelectorAll('.one2many-editor, .o2m-table, .o2m-row').length,
      visible_error: clean(document.querySelector('.status-panel.error, .validation-error')?.textContent || ''),
      text_sample: clean(shell?.textContent || '').slice(0, 600),
    };
  });
}

async function inspectSpecimen(page, specimen) {
  const contract = await intentRequest(page, 'load_contract', {
    model: specimen.model,
    view_type: 'form',
    include: 'all',
    action_id: Number(specimen.actionId || 0) || undefined,
    menu_id: Number(specimen.menuId || 0) || undefined,
  });
  const contractInfo = contractSummary(contract);
  await openForm(page, specimen);
  const domInfo = await domSummary(page);
  const hasRenderableSurface = domInfo.input_count > 0
    || domInfo.field_count > 0
    || domInfo.readonly_count > 0
    || domInfo.tabs.length > 0
    || domInfo.statusbar_count > 0
    || domInfo.o2m_count > 0
    || hasReadonlyProjectionSurface(specimen, contractInfo, domInfo);
  const contractOk = contractInfo.form_present && contractInfo.field_count > 0;
  return {
    ...specimen,
    contract: contractInfo,
    dom: domInfo,
    status: contractOk && hasRenderableSurface && !domInfo.visible_error ? 'pass' : 'fail',
    checks: { contractOk, hasRenderableSurface, noVisibleError: !domInfo.visible_error },
  };
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const result = {
    db: DB_NAME,
    login: LOGIN,
    frontend_url: FRONTEND_URL,
    artifacts: outDir,
    specimens: SPECIMENS,
    rows: [],
    paths: [],
  };

  try {
    const context = await browser.newContext({ locale: 'zh-CN' });
    const page = await context.newPage();
    attachConsoleCapture(page);
    await login(page);

    for (const specimen of SPECIMENS) {
      const row = await inspectSpecimen(page, specimen);
      result.rows.push(row);
      await page.screenshot({
        path: path.join(outDir, `${row.tier}-${row.model.replace(/\./g, '_')}-${row.recordId}.png`),
        fullPage: true,
      });
    }

    result.console_errors = page.__consoleErrors || [];
    result.paths.push({
      path_id: 'L6-M2-M5',
      level: 'L6',
      name: 'representative form tier surface reachability',
      status: result.rows.every((row) => row.status === 'pass') && result.console_errors.length === 0 ? 'pass' : 'fail',
      rows: result.rows.map((row) => ({
        tier: row.tier,
        model: row.model,
        record_id: row.recordId,
        status: row.status,
        checks: row.checks,
      })),
    });
    await context.close();
    result.pass = result.paths.every((row) => row.status === 'pass');
    writeJson('summary.json', result);
    console.log(`[form_model_tier_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: result.pass,
      paths: result.paths,
      console_errors: result.console_errors.length,
    }, null, 2));
    process.exit(result.pass ? 0 : 1);
  } catch (err) {
    result.pass = false;
    result.error = err instanceof Error ? err.message : String(err);
    writeJson('summary.json', result);
    console.error(`[form_model_tier_acceptance] failed artifacts=${outDir}`);
    console.error(result.error);
    process.exit(1);
  } finally {
    await browser.close().catch(() => {});
  }
}

main();
