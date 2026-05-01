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
const LOGIN = process.env.E2E_LOGIN || 'caisiqi';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ACTION_ID = Number(process.env.ACTION_ID || 549);
const PARTNER_ID = Number(process.env.PARTNER_ID || 7980);
const PICKING_TYPE_ID = Number(process.env.PICKING_TYPE_ID || 1);
const PRODUCT_ID = Number(process.env.PRODUCT_ID || 1);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-m3-purchase-order-line', ts);

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

function actionableConsoleErrors(summary) {
  const errors = Array.isArray(summary.console_errors) ? summary.console_errors : [];
  const expectedDeletePolicyDenied = summary.fixture_cleanup?.public_unlink_denied === true
    && summary.fixture_cleanup?.requires_shell_cleanup === true;
  if (!expectedDeletePolicyDenied) return errors;
  return errors.filter((text) => !String(text || '').includes('403 (FORBIDDEN)'));
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

async function intentRequest(page, intent, params) {
  const authToken = await token(page);
  return page.evaluate(async ({ dbName, authToken: bearer, intentName, payload }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: bearer ? `Bearer ${bearer}` : '',
        'X-Trace-Id': `form-m3-po-line-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params: payload }),
    });
    const body = await response.json().catch(() => ({}));
    return {
      status: response.status,
      ok: body.ok === true,
      data: body.data || {},
      error: body.error || {},
      meta: body.meta || {},
    };
  }, { dbName: DB_NAME, authToken, intentName: intent, payload: params });
}

async function createFixtureOrder(page) {
  const created = await intentRequest(page, 'api.data', {
    op: 'create',
    model: 'purchase.order',
    vals: {
      partner_id: PARTNER_ID,
      picking_type_id: PICKING_TYPE_ID,
      date_order: new Date().toISOString().slice(0, 10),
    },
    context: {},
  });
  if (!created.ok || !Number(created.data?.id)) {
    throw new Error(`fixture purchase.order create failed: ${JSON.stringify(created.error || created.data)}`);
  }
  return Number(created.data.id);
}

async function cleanupFixtureOrder(page, orderId) {
  const cleanup = {
    order_id: orderId,
    line_ids_before: [],
    public_unlink_denied: false,
    requires_shell_cleanup: false,
    errors: [],
  };
  if (!orderId) return cleanup;
  try {
    const read = await readOrder(page, orderId);
    cleanup.line_ids_before = read.order_line_ids;
  } catch (err) {
    cleanup.errors.push(`read_before_cleanup: ${err instanceof Error ? err.message : String(err)}`);
  }
  try {
    const resp = await intentRequest(page, 'api.data.unlink', {
      model: 'purchase.order',
      ids: [orderId],
      context: {},
    });
    if (resp.ok === true) {
      cleanup.public_unlink_denied = false;
      cleanup.requires_shell_cleanup = false;
    } else if (normalize(resp.error?.reason_code || resp.error?.code) === 'DELETE_POLICY_DENIED') {
      cleanup.public_unlink_denied = true;
      cleanup.requires_shell_cleanup = true;
    } else {
      cleanup.errors.push(`unlink_order: ${JSON.stringify(resp.error || resp.data)}`);
    }
  } catch (err) {
    cleanup.errors.push(`unlink_order: ${err instanceof Error ? err.message : String(err)}`);
  }
  return cleanup;
}

async function readOrder(page, orderId) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'purchase.order',
    ids: [orderId],
    fields: ['id', 'name', 'state', 'order_line'],
    context: {},
  });
  if (!resp.ok) throw new Error(`read purchase.order failed: ${JSON.stringify(resp.error || resp.data)}`);
  const record = Array.isArray(resp.data?.records) ? resp.data.records[0] || {} : {};
  const rawLine = record.order_line;
  const lineIds = Array.isArray(rawLine)
    ? rawLine.map((item) => Array.isArray(item) ? Number(item[0]) : Number(item)).filter((id) => Number.isFinite(id) && id > 0)
    : [];
  return { record, order_line_ids: lineIds };
}

async function readLines(page, lineIds) {
  if (!lineIds.length) return [];
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'purchase.order.line',
    ids: lineIds,
    fields: ['id', 'name', 'product_id', 'product_uom', 'product_qty', 'price_unit', 'price_subtotal'],
    context: {},
  });
  if (!resp.ok) throw new Error(`read purchase.order.line failed: ${JSON.stringify(resp.error || resp.data)}`);
  return Array.isArray(resp.data?.records) ? resp.data.records : [];
}

async function openOrderForm(page, orderId) {
  await page.goto(`${FRONTEND_URL}/r/purchase.order/${orderId}?action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function orderLineSurface(page) {
  return page.evaluate(() => {
    const text = (node) => String(node?.textContent || '').replace(/\s+/g, ' ').trim();
    const editors = Array.from(document.querySelectorAll('.relation-editor'));
    const target = editors.find((editor) => text(editor).includes('描述') && text(editor).includes('数量') && text(editor).includes('单价')) || null;
    return {
      found: Boolean(target),
      headers: target ? Array.from(target.querySelectorAll('.o2m-header-cell')).map(text).filter(Boolean) : [],
      row_count: target ? target.querySelectorAll('.o2m-row').length : 0,
      can_add: target ? Array.from(target.querySelectorAll('.o2m-toolbar button')).map(text).includes('添加行') : false,
      readonly_headers: target ? Array.from(target.querySelectorAll('.o2m-header-cell')).map(text).filter((label) => label.includes('小计')) : [],
      shell_sample: text(document.querySelector('.template-layout-shell')).slice(0, 900),
    };
  });
}

async function clickAddOrderLine(page) {
  const addButton = page.locator('.relation-editor').filter({ hasText: '描述' }).filter({ hasText: '数量' }).filter({ hasText: '单价' })
    .locator('.o2m-toolbar button').filter({ hasText: /^添加行$/ }).first();
  await addButton.click();
  await page.locator('.relation-editor').filter({ hasText: '描述' }).locator('.o2m-row').first().waitFor({ timeout: 10000 });
}

async function fillLineField(page, rowIndex, label, value) {
  const row = page.locator('.relation-editor').filter({ hasText: '描述' }).filter({ hasText: '数量' }).filter({ hasText: '单价' })
    .locator('.o2m-row').nth(rowIndex);
  const field = row.locator('label.o2m-field').filter({ hasText: label }).first();
  const input = field.locator('input.input, textarea.input, select.input').first();
  await input.fill(String(value));
}

async function saveForm(page) {
  const save = page.locator('.template-page-header-actions button.primary').filter({ hasText: /^保存$/ }).first();
  await save.waitFor({ timeout: 10000 });
  await save.click();
  const success = page.getByText('保存成功，已同步最新表单内容。', { exact: true });
  await success.waitFor({ timeout: 20000 }).catch(async (err) => {
    const visibleError = normalize(await page.locator('.validation-error, .submission-feedback--error, .submission-feedback--warn, .status-panel.error').first().innerText().catch(() => ''));
    throw new Error(`save did not report success${visibleError ? `; visible_error=${visibleError}` : ''}; ${err.message}`);
  });
}

async function removeFirstLine(page) {
  const row = page.locator('.relation-editor').filter({ hasText: '描述' }).filter({ hasText: '数量' }).filter({ hasText: '单价' })
    .locator('.o2m-row').first();
  await row.locator('button.ghost').filter({ hasText: /^移除$/ }).click();
}

async function assertNoVisibleError(page) {
  const visibleError = normalize(await page.locator('.validation-error, .submission-feedback--error, .status-panel.error').first().innerText().catch(() => ''));
  return visibleError;
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
  attachConsoleCapture(page);
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: 'purchase.order',
    action_id: ACTION_ID,
    partner_id: PARTNER_ID,
    picking_type_id: PICKING_TYPE_ID,
    product_id: PRODUCT_ID,
    artifact_dir: outDir,
    checks: [],
  };
  let orderId = 0;
  try {
    await login(page);
    orderId = await createFixtureOrder(page);
    summary.fixture_order_id = orderId;
    await openOrderForm(page, orderId);

    const surface = await orderLineSurface(page);
    summary.checks.push({
      path_id: 'M3-P12/P13',
      name: 'purchase order line surface exposes editable and readonly business columns',
      status: surface.found
        && surface.can_add
        && ['描述*', '数量*', '单价*'].every((label) => surface.headers.includes(label))
        && surface.headers.some((label) => label.includes('小计'))
        ? 'pass'
        : 'fail',
      surface,
    });

    const lineName = `M3 line acceptance ${Date.now()}`;
    await clickAddOrderLine(page);
    await fillLineField(page, 0, '产品', String(PRODUCT_ID));
    await fillLineField(page, 0, '描述', lineName);
    await fillLineField(page, 0, '数量', '2');
    await fillLineField(page, 0, '单价', '9.5');
    await saveForm(page);
    await openOrderForm(page, orderId);
    let order = await readOrder(page, orderId);
    let lines = await readLines(page, order.order_line_ids);
    summary.checks.push({
      path_id: 'M3-P12/P23',
      name: 'browser adds purchase order line and persistence is readable after reload',
      status: lines.length === 1
        && normalize(lines[0].name) === lineName
        && Array.isArray(lines[0].product_id)
        && Number(lines[0].product_id[0]) === PRODUCT_ID
        && Array.isArray(lines[0].product_uom)
        && Number(lines[0].product_uom[0]) > 0
        && Number(lines[0].product_qty) === 2
        && Number(lines[0].price_unit) === 9.5
        ? 'pass'
        : 'fail',
      order_line_ids: order.order_line_ids,
      lines,
    });

    await fillLineField(page, 0, '数量', '3');
    await fillLineField(page, 0, '单价', '12.25');
    await saveForm(page);
    await openOrderForm(page, orderId);
    order = await readOrder(page, orderId);
    lines = await readLines(page, order.order_line_ids);
    summary.checks.push({
      path_id: 'M3-P12/P23',
      name: 'browser edits purchase order line numeric fields and persistence is readable after reload',
      status: lines.length === 1
        && normalize(lines[0].name) === lineName
        && Number(lines[0].product_qty) === 3
        && Number(lines[0].price_unit) === 12.25
        ? 'pass'
        : 'fail',
      order_line_ids: order.order_line_ids,
      lines,
    });

    await removeFirstLine(page);
    await saveForm(page);
    await openOrderForm(page, orderId);
    order = await readOrder(page, orderId);
    summary.checks.push({
      path_id: 'M3-P12/P23',
      name: 'browser removes purchase order line and persistence is empty after reload',
      status: order.order_line_ids.length === 0 ? 'pass' : 'fail',
      order_line_ids: order.order_line_ids,
    });

    const visibleError = await assertNoVisibleError(page);
    summary.checks.push({
      path_id: 'M3-P20',
      name: 'line lifecycle does not expose user-visible technical error',
      status: visibleError ? 'fail' : 'pass',
      visible_error: visibleError,
    });

    summary.console_errors = page.__consoleErrors || [];
  } finally {
    if (orderId) {
      summary.fixture_cleanup = await cleanupFixtureOrder(page, orderId).catch((err) => ({
        order_id: orderId,
        unlinked_order: false,
        errors: [err instanceof Error ? err.message : String(err)],
      }));
    }
    await page.screenshot({ path: path.join(outDir, 'purchase_order_line_final.png'), fullPage: true }).catch(() => {});
    await browser.close();
  }

  summary.actionable_console_errors = actionableConsoleErrors(summary);
  summary.pass = summary.checks.every((row) => row.status === 'pass')
    && (summary.actionable_console_errors || []).length === 0
    && summary.fixture_cleanup?.public_unlink_denied === true
    && summary.fixture_cleanup?.requires_shell_cleanup === true
    && (summary.fixture_cleanup?.errors || []).length === 0;
  writeJson('summary.json', summary);
  console.log(`[form_m3_purchase_order_line_acceptance] artifacts=${outDir}`);
  console.log(JSON.stringify({
    pass: summary.pass,
    fixture_order_id: summary.fixture_order_id,
    checks: summary.checks.map((row) => ({ name: row.name, status: row.status })),
    cleanup: summary.fixture_cleanup,
    console_errors: (summary.console_errors || []).length,
    actionable_console_errors: (summary.actionable_console_errors || []).length,
  }, null, 2));
  if (!summary.pass) process.exit(1);
}

main().catch((err) => {
  const summary = {
    pass: false,
    error: err instanceof Error ? err.message : String(err),
    artifact_dir: outDir,
  };
  writeJson('summary.json', summary);
  console.error(JSON.stringify(summary, null, 2));
  process.exit(1);
});
