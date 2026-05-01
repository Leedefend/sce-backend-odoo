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
const ACTION_ID = Number(process.env.ACTION_ID || 619);
const RECORD_ID = Number(process.env.RECORD_ID || 5);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-m5-dictionary-maintenance', ts);

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
        'X-Trace-Id': `form-m5-dictionary-${Date.now()}`,
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

async function openCreate(page) {
  await page.goto(`${FRONTEND_URL}/f/sc.dictionary/new?action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
}

async function openRecord(page, id) {
  await page.goto(`${FRONTEND_URL}/r/sc.dictionary/${id}?action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function fillFieldByLabel(page, label, value) {
  const ok = await page.evaluate(({ labelText, fieldValue }) => {
    const normalizeText = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const fields = Array.from(document.querySelectorAll('.field'));
    const target = fields.find((field) => normalizeText(field.querySelector('.label')?.textContent).replace(/\*$/, '') === labelText);
    if (!target) return false;
    const input = target.querySelector('input.input, textarea.input, select.input');
    if (!input) return false;
    input.value = String(fieldValue);
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }, { labelText: label, fieldValue: value });
  if (!ok) throw new Error(`field not found or not editable: ${label}`);
}

async function selectFieldByLabel(page, label, optionValue) {
  await fillFieldByLabel(page, label, optionValue);
}

async function saveForm(page) {
  const save = page.locator('.template-page-header-actions button.primary').filter({ hasText: /^保存$/ }).first();
  await save.waitFor({ timeout: 10000 });
  await save.click();
}

async function visibleFeedback(page) {
  return normalize(await page.locator('.validation-error, .submission-feedback--error, .submission-feedback--warn, .status-panel.error').first().innerText().catch(() => ''));
}

async function readDictionary(page, ids) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'sc.dictionary',
    ids,
    fields: ['id', 'name', 'code', 'type', 'active', 'display_name'],
    context: {},
  });
  if (!resp.ok) throw new Error(`read sc.dictionary failed: ${JSON.stringify(resp.error || resp.data)}`);
  return Array.isArray(resp.data?.records) ? resp.data.records : [];
}

async function listAcceptanceRows(page, code) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'list',
    model: 'sc.dictionary',
    fields: ['id', 'name', 'code', 'type', 'active', 'display_name'],
    domain: [['code', '=', code]],
    limit: 20,
    context: {},
  });
  if (!resp.ok) throw new Error(`list sc.dictionary failed: ${JSON.stringify(resp.error || resp.data)}`);
  return Array.isArray(resp.data?.records) ? resp.data.records : [];
}

async function waitForDictionaryRows(page, code, predicate, timeoutMs = 20000) {
  const deadline = Date.now() + timeoutMs;
  let rows = [];
  while (Date.now() < deadline) {
    rows = await listAcceptanceRows(page, code);
    if (predicate(rows)) return rows;
    await page.waitForTimeout(500);
  }
  return rows;
}

async function unlinkDictionary(page, ids) {
  if (!ids.length) return { skipped: true, ids: [] };
  return intentRequest(page, 'api.data.unlink', {
    model: 'sc.dictionary',
    ids,
    context: {},
  });
}

async function cleanup(page, code) {
  const rows = await listAcceptanceRows(page, code).catch(() => []);
  const ids = rows.map((row) => Number(row.id)).filter((id) => Number.isFinite(id) && id > 0);
  const result = {
    code,
    ids,
    public_unlink_ok: false,
    public_unlink_denied: false,
    requires_shell_cleanup: false,
    errors: [],
  };
  if (!ids.length) return result;
  try {
    const resp = await unlinkDictionary(page, ids);
    result.public_unlink_ok = resp.ok === true;
    if (!resp.ok && normalize(resp.error?.reason_code || resp.error?.code) === 'DELETE_POLICY_DENIED') {
      result.public_unlink_denied = true;
      result.requires_shell_cleanup = true;
    } else if (!resp.ok) {
      result.errors.push(JSON.stringify(resp.error || resp.data));
    }
  } catch (err) {
    result.errors.push(err instanceof Error ? err.message : String(err));
  }
  return result;
}

async function formSurface(page) {
  return page.evaluate(() => {
    const normalizeText = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return {
      labels: Array.from(document.querySelectorAll('.field .label')).map((node) => normalizeText(node.textContent)).filter(Boolean),
      inputs: document.querySelectorAll('.field input.input, .field textarea.input, .field select.input').length,
      text_sample: normalizeText(document.querySelector('.template-layout-shell')?.textContent).slice(0, 900),
    };
  });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
  attachConsoleCapture(page);
  const unique = Date.now();
  const code = `M5ACC${unique}`;
  const name = `M5 acceptance ${unique}`;
  const editedName = `${name} edited`;
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: 'sc.dictionary',
    action_id: ACTION_ID,
    artifact_dir: outDir,
    fixture_code: code,
    checks: [],
  };
  let createdId = 0;

  try {
    await login(page);
    await cleanup(page, code);

    await openCreate(page);
    const createSurface = await formSurface(page);
    summary.checks.push({
      path_id: 'M5-P03/P05',
      name: 'create form exposes business maintenance fields without technical clutter',
      status: ['名称*', '编码', '字典类型*', '排序'].every((label) => createSurface.labels.includes(label))
        && !createSurface.labels.some((label) => ['ID', '创建人', '创建时间', '最后更新人', '最后更新时间'].includes(label.replace(/\*$/, '')))
        ? 'pass'
        : 'fail',
      surface: createSurface,
    });

    await fillFieldByLabel(page, '名称', name);
    await fillFieldByLabel(page, '编码', code);
    await selectFieldByLabel(page, '字典类型', 'project_type');
    await saveForm(page);
    const rows = await waitForDictionaryRows(page, code, (items) => items.length === 1);
    createdId = Number(rows[0]?.id || 0);
    summary.fixture_id = createdId;
    summary.checks.push({
      path_id: 'M5-P03/P23',
      name: 'browser creates dictionary record and persistence is readable',
      status: rows.length === 1
        && normalize(rows[0].name) === name
        && normalize(rows[0].code) === code
        && normalize(rows[0].type) === 'project_type'
        ? 'pass'
        : 'fail',
      rows,
    });

    await openRecord(page, createdId);
    await fillFieldByLabel(page, '名称', editedName);
    await saveForm(page);
    await waitForDictionaryRows(page, code, (items) => items.length === 1 && normalize(items[0].name) === editedName);
    const afterEdit = await readDictionary(page, [createdId]);
    summary.checks.push({
      path_id: 'M5-P04/P23',
      name: 'browser edits dictionary record and persistence is readable after reload',
      status: afterEdit.length === 1 && normalize(afterEdit[0].name) === editedName ? 'pass' : 'fail',
      rows: afterEdit,
    });

    await openCreate(page);
    await fillFieldByLabel(page, '名称', `${name} duplicate`);
    await fillFieldByLabel(page, '编码', code);
    await selectFieldByLabel(page, '字典类型', 'project_type');
    await saveForm(page);
    await page.waitForTimeout(1500);
    const duplicateFeedback = await visibleFeedback(page);
    const allRowsAfterDuplicate = await listAcceptanceRows(page, code);
    summary.checks.push({
      path_id: 'M5-P20',
      name: 'duplicate code/type shows friendly error and does not create a second record',
      status: duplicateFeedback.includes('已有相同记录')
        && !/duplicate key|psycopg2|Traceback|DETAIL:/i.test(duplicateFeedback)
        && allRowsAfterDuplicate.length === 1
        ? 'pass'
        : 'fail',
      feedback: duplicateFeedback,
      rows: allRowsAfterDuplicate,
    });

    summary.console_errors = page.__consoleErrors || [];
  } finally {
    summary.fixture_cleanup = await cleanup(page, code).catch((err) => ({
      code,
      errors: [err instanceof Error ? err.message : String(err)],
    }));
    await page.screenshot({ path: path.join(outDir, 'dictionary_final.png'), fullPage: true }).catch(() => {});
    await browser.close();
  }

  summary.actionable_console_errors = actionableConsoleErrors(summary);
  summary.pass = summary.checks.every((row) => row.status === 'pass')
    && (summary.actionable_console_errors || []).length === 0
    && (
      summary.fixture_cleanup?.public_unlink_ok === true
      || (
        summary.fixture_cleanup?.public_unlink_denied === true
        && summary.fixture_cleanup?.requires_shell_cleanup === true
      )
    )
    && (summary.fixture_cleanup?.errors || []).length === 0;
  writeJson('summary.json', summary);
  console.log(`[form_m5_dictionary_maintenance_acceptance] artifacts=${outDir}`);
  console.log(JSON.stringify({
    pass: summary.pass,
    fixture_id: summary.fixture_id,
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
