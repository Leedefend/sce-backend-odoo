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
const ACTION_ID = Number(process.env.ACTION_ID || 511);
const PROJECT_ID = Number(process.env.PROJECT_ID || 514);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-primitive-numeric-date', ts);

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
        'X-Trace-Id': `form-primitive-numeric-date-${Date.now()}`,
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

async function createRecord(page, model, vals, context = {}) {
  const resp = await intentRequest(page, 'api.data', { op: 'create', model, vals, context });
  if (!resp.ok || !Number(resp.data?.id)) {
    throw new Error(`create ${model} failed: ${JSON.stringify(resp.error || resp.data)}`);
  }
  return Number(resp.data.id);
}

async function listRecords(page, model, domain, fields) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'list',
    model,
    domain,
    fields,
    limit: 50,
    context: {},
  });
  if (!resp.ok) throw new Error(`list ${model} failed: ${JSON.stringify(resp.error || resp.data)}`);
  return Array.isArray(resp.data?.records) ? resp.data.records : [];
}

async function readLedger(page, id) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'project.cost.ledger',
    ids: [id],
    fields: ['id', 'date', 'qty', 'amount', 'note', 'source_model', 'source_id'],
    context: {},
  });
  if (!resp.ok) throw new Error(`read project.cost.ledger failed: ${JSON.stringify(resp.error || resp.data)}`);
  return Array.isArray(resp.data?.records) ? resp.data.records[0] || null : null;
}

async function unlinkPublic(page, model, ids) {
  if (!ids.length) return { skipped: true, ids: [] };
  return intentRequest(page, 'api.data.unlink', { model, ids, context: {} });
}

function safeSourceId(marker) {
  return Number(marker) % 1000000000;
}

async function cleanup(page, marker, sourceId = safeSourceId(marker)) {
  const ledgers = await listRecords(
    page,
    'project.cost.ledger',
    [['source_model', '=', 'p06_primitive_numeric_date'], ['source_id', '=', sourceId]],
    ['id'],
  ).catch(() => []);
  const periods = await listRecords(
    page,
    'project.cost.period',
    [['period', '=', `2099-10-P06B-${marker}`]],
    ['id'],
  ).catch(() => []);
  const codes = await listRecords(
    page,
    'project.cost.code',
    [['code', '=', `P06B${marker}`]],
    ['id'],
  ).catch(() => []);
  const result = {
    marker,
    source_id: sourceId,
    ledger_ids: ledgers.map((row) => Number(row.id)).filter(Boolean),
    period_ids: periods.map((row) => Number(row.id)).filter(Boolean),
    cost_code_ids: codes.map((row) => Number(row.id)).filter(Boolean),
    public_unlink_denied: false,
    requires_shell_cleanup: false,
    errors: [],
  };
  for (const [model, ids] of [
    ['project.cost.ledger', result.ledger_ids],
    ['project.cost.period', result.period_ids],
    ['project.cost.code', result.cost_code_ids],
  ]) {
    if (!ids.length) continue;
    const resp = await unlinkPublic(page, model, ids).catch((err) => ({
      ok: false,
      error: { message: err instanceof Error ? err.message : String(err) },
    }));
    if (!resp.ok) {
      result.public_unlink_denied = true;
      result.requires_shell_cleanup = true;
      const code = normalize(resp.error?.reason_code || resp.error?.code || resp.error?.message);
      if (code && code !== 'DELETE_POLICY_DENIED') result.errors.push(`${model}: ${code}`);
    }
  }
  return result;
}

function actionableConsoleErrors(summary) {
  const errors = Array.isArray(summary.console_errors) ? summary.console_errors : [];
  if (!summary.fixture_cleanup?.requires_shell_cleanup) return errors;
  return errors.filter((text) => !String(text || '').includes('403 (FORBIDDEN)'));
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function openLedger(page, id) {
  await page.goto(`${FRONTEND_URL}/r/project.cost.ledger/${id}?action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
}

async function fieldSurface(page) {
  return page.evaluate(() => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return Array.from(document.querySelectorAll('.field')).map((field) => {
      const input = field.querySelector('input.input, input.input-checkbox, textarea.input, select.input');
      return {
        label: clean(field.querySelector('.label')?.textContent || '').replace(/\*$/, ''),
        tag: input?.tagName?.toLowerCase() || '',
        type: input?.getAttribute('type') || '',
        value: input?.tagName === 'INPUT' && input.getAttribute('type') === 'checkbox'
          ? Boolean(input.checked)
          : input?.value || '',
        disabled: Boolean(input?.disabled),
        text: clean(field.textContent).slice(0, 160),
      };
    }).filter((item) => item.label);
  });
}

async function setFieldByLabel(page, label, value) {
  const ok = await page.evaluate(({ labelText, fieldValue }) => {
    const clean = (val) => String(val || '').replace(/\s+/g, ' ').trim();
    const fields = Array.from(document.querySelectorAll('.field'));
    const target = fields.find((field) => clean(field.querySelector('.label')?.textContent || '').replace(/\*$/, '') === labelText);
    if (!target) return false;
    const input = target.querySelector('input.input, input.input-checkbox, textarea.input, select.input');
    if (!input) return false;
    if (input.tagName === 'INPUT' && input.getAttribute('type') === 'checkbox') {
      input.checked = Boolean(fieldValue);
    } else {
      input.value = String(fieldValue);
    }
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }, { labelText: label, fieldValue: value });
  if (!ok) throw new Error(`field not found or not editable: ${label}`);
}

async function saveForm(page) {
  const save = page.locator('.template-page-header-actions button.primary').filter({ hasText: /^保存$/ }).first();
  await save.waitFor({ timeout: 10000 });
  await save.click();
  await page.getByText('保存成功，已同步最新表单内容。', { exact: true }).waitFor({ timeout: 15000 });
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
  attachConsoleCapture(page);

  const marker = Date.now();
  const sourceId = safeSourceId(marker);
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: 'project.cost.ledger',
    action_id: ACTION_ID,
    artifact_dir: outDir,
    marker,
    source_id: sourceId,
    checks: [],
  };

  try {
    await login(page);
    await cleanup(page, marker, sourceId);
    const costCodeId = await createRecord(page, 'project.cost.code', {
      name: `P06B cost ${marker}`,
      code: `P06B${marker}`,
      type: 'other',
    });
    const periodId = await createRecord(page, 'project.cost.period', {
      project_id: PROJECT_ID,
      period: `2099-10-P06B-${marker}`,
    });
    const ledgerId = await createRecord(page, 'project.cost.ledger', {
      project_id: PROJECT_ID,
      cost_code_id: costCodeId,
      period_id: periodId,
      date: '2099-10-10',
      qty: 1.25,
      amount: 88.66,
      note: `P06B note ${marker}`,
      source_model: 'p06_primitive_numeric_date',
      source_id: sourceId,
    });
    summary.fixture_ids = { cost_code_id: costCodeId, period_id: periodId, ledger_id: ledgerId };

    await openLedger(page, ledgerId);
    const surface = await fieldSurface(page);
    const byLabel = Object.fromEntries(surface.map((row) => [row.label, row]));
    summary.checks.push({
      path_id: 'P06',
      name: 'date, float, and monetary controls render from contract-backed field types',
      status: byLabel['发生日期']?.type === 'date'
        && byLabel['数量']?.type === 'number'
        && byLabel['金额']?.type === 'number'
        ? 'pass'
        : 'fail',
      surface,
    });

    await setFieldByLabel(page, '发生日期', '2099-10-11');
    await setFieldByLabel(page, '数量', '2.75');
    await setFieldByLabel(page, '金额', '166.88');
    await setFieldByLabel(page, '备注/摘要', `P06B edited ${marker}`);
    await saveForm(page);
    const afterEdit = await readLedger(page, ledgerId);
    await openLedger(page, ledgerId);
    const afterReloadSurface = await fieldSurface(page);
    summary.checks.push({
      path_id: 'P06/P04/P23',
      name: 'date, float, monetary, and note values edit, persist, and reload',
      status: normalize(afterEdit?.date) === '2099-10-11'
        && Number(afterEdit?.qty) === 2.75
        && Number(afterEdit?.amount) === 166.88
        && normalize(afterEdit?.note) === `P06B edited ${marker}`
        && afterReloadSurface.some((row) => row.label === '发生日期' && row.value === '2099-10-11')
        && afterReloadSurface.some((row) => row.label === '数量' && Number(row.value) === 2.75)
        && afterReloadSurface.some((row) => row.label === '金额' && Number(row.value) === 166.88)
        ? 'pass'
        : 'fail',
      after_edit: afterEdit,
      after_reload_surface: afterReloadSurface,
    });

    summary.console_errors = page.__consoleErrors || [];
    await page.screenshot({ path: path.join(outDir, 'numeric_date_final.png'), fullPage: true });
  } finally {
    summary.fixture_cleanup = await cleanup(page, marker, sourceId).catch((err) => ({
      marker,
      source_id: sourceId,
      errors: [err instanceof Error ? err.message : String(err)],
    }));
    await browser.close().catch(() => {});
  }

  summary.actionable_console_errors = actionableConsoleErrors(summary);
  summary.pass = summary.checks.every((check) => check.status === 'pass')
    && summary.actionable_console_errors.length === 0
    && !summary.fixture_cleanup?.errors?.length;
  writeJson('summary.json', summary);
  console.log(`[form_primitive_numeric_date_acceptance] artifacts=${outDir}`);
  console.log(JSON.stringify({
    pass: summary.pass,
    checks: summary.checks.map((check) => ({ name: check.name, status: check.status })),
    fixture_ids: summary.fixture_ids,
    cleanup: summary.fixture_cleanup,
    actionable_console_errors: summary.actionable_console_errors.length,
  }, null, 2));
  if (!summary.pass) process.exit(1);
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[form_primitive_numeric_date_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
