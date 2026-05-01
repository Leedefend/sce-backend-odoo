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
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-concurrency-conflict', ts);

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
        'X-Trace-Id': `form-concurrency-conflict-${Date.now()}`,
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

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function openRecord(page, id) {
  await page.goto(`${FRONTEND_URL}/r/sc.dictionary/${id}?action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
}

async function fillFieldByLabel(page, label, value) {
  const ok = await page.evaluate(({ labelText, fieldValue }) => {
    const normalizeText = (val) => String(val || '').replace(/\s+/g, ' ').trim();
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

async function fieldValueByLabel(page, label) {
  return page.evaluate((labelText) => {
    const normalizeText = (val) => String(val || '').replace(/\s+/g, ' ').trim();
    const fields = Array.from(document.querySelectorAll('.field'));
    const target = fields.find((field) => normalizeText(field.querySelector('.label')?.textContent).replace(/\*$/, '') === labelText);
    const input = target?.querySelector('input.input, textarea.input, select.input');
    return input ? input.value : '';
  }, label);
}

async function waitForFieldValueByLabel(page, label, expected) {
  await page.waitForFunction(({ labelText, expectedValue }) => {
    const normalizeText = (val) => String(val || '').replace(/\s+/g, ' ').trim();
    const fields = Array.from(document.querySelectorAll('.field'));
    const target = fields.find((field) => normalizeText(field.querySelector('.label')?.textContent).replace(/\*$/, '') === labelText);
    const input = target?.querySelector('input.input, textarea.input, select.input');
    return input && normalizeText(input.value) === normalizeText(expectedValue);
  }, { labelText: label, expectedValue: expected }, { timeout: 15000 });
}

async function saveForm(page) {
  const save = page.locator('.template-page-header-actions button.primary').filter({ hasText: /^保存$/ }).first();
  await save.waitFor({ timeout: 10000 });
  await save.click();
}

async function visibleFeedback(page) {
  return normalize(await page.locator('.validation-error, .submission-feedback--error, .submission-feedback--warn, .status-panel.error, .status-panel').first().innerText().catch(() => ''));
}

async function waitForSaveSuccess(page) {
  await page.getByText('保存成功，已同步最新表单内容。', { exact: true }).waitFor({ timeout: 15000 });
}

async function createDictionary(page, code, name) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'create',
    model: 'sc.dictionary',
    vals: {
      name,
      code,
      type: 'project_type',
      sequence: 90,
      active: true,
    },
    context: {},
  });
  if (!resp.ok || !Number(resp.data?.id)) {
    throw new Error(`create sc.dictionary failed: ${JSON.stringify(resp.error || resp.data)}`);
  }
  return Number(resp.data.id);
}

async function readDictionary(page, id) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'sc.dictionary',
    ids: [id],
    fields: ['id', 'name', 'code', 'type', 'active', 'write_date'],
    context: {},
  });
  if (!resp.ok) throw new Error(`read sc.dictionary failed: ${JSON.stringify(resp.error || resp.data)}`);
  const rows = Array.isArray(resp.data?.records) ? resp.data.records : [];
  return rows[0] || null;
}

async function listDictionary(page, code) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'list',
    model: 'sc.dictionary',
    fields: ['id', 'name', 'code', 'type', 'active'],
    domain: [['code', '=', code]],
    limit: 20,
    context: {},
  });
  if (!resp.ok) throw new Error(`list sc.dictionary failed: ${JSON.stringify(resp.error || resp.data)}`);
  return Array.isArray(resp.data?.records) ? resp.data.records : [];
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
  const rows = await listDictionary(page, code).catch(() => []);
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

function actionableConsoleErrors(summary) {
  const errors = [
    ...(Array.isArray(summary.console_errors?.first_tab) ? summary.console_errors.first_tab : []),
    ...(Array.isArray(summary.console_errors?.second_tab) ? summary.console_errors.second_tab : []),
  ];
  const expectedDeletePolicyDenied = summary.fixture_cleanup?.public_unlink_denied === true
    && summary.fixture_cleanup?.requires_shell_cleanup === true;
  if (!expectedDeletePolicyDenied) return errors;
  return errors.filter((text) => !String(text || '').includes('403 (FORBIDDEN)'));
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const contextA = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
  const contextB = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
  const pageA = await contextA.newPage();
  const pageB = await contextB.newPage();
  attachConsoleCapture(pageA);
  attachConsoleCapture(pageB);

  const unique = Date.now();
  const code = `P24CONFLICT${unique}`;
  const initialName = `P24 conflict fixture ${unique}`;
  const secondTabName = `${initialName} second tab saved`;
  const staleTabName = `${initialName} stale tab blocked`;
  const recoveredName = `${initialName} recovered after reload`;
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: 'sc.dictionary',
    action_id: ACTION_ID,
    artifact_dir: outDir,
    fixture_code: code,
    fixture_id: 0,
    checks: [],
  };

  try {
    await login(pageA);
    await login(pageB);
    await cleanup(pageA, code);
    const createdId = await createDictionary(pageA, code, initialName);
    summary.fixture_id = createdId;

    await openRecord(pageA, createdId);
    await openRecord(pageB, createdId);
    const initialRead = await readDictionary(pageA, createdId);

    await fillFieldByLabel(pageB, '名称', secondTabName);
    await saveForm(pageB);
    await waitForSaveSuccess(pageB);
    const afterSecondSave = await readDictionary(pageA, createdId);

    await fillFieldByLabel(pageA, '名称', staleTabName);
    await saveForm(pageA);
    await pageA.waitForTimeout(1500);
    const staleFeedback = await visibleFeedback(pageA);
    const afterStaleAttempt = await readDictionary(pageA, createdId);

    const conflictFriendly = /数据已被其他操作更新|重新加载后再保存|RECORD_VERSION_CONFLICT/.test(staleFeedback);
    const staleBlocked = normalize(afterStaleAttempt?.name) === secondTabName;
    const noRawTrace = !/Traceback|psycopg2|stack trace|Internal Server Error/i.test(staleFeedback);
    summary.checks.push({
      path_id: 'P24',
      name: 'two browser tabs stale save is rejected with friendly conflict feedback',
      status: conflictFriendly && staleBlocked && noRawTrace ? 'pass' : 'fail',
      initial_read: initialRead,
      after_second_save: afterSecondSave,
      stale_feedback: staleFeedback,
      after_stale_attempt: afterStaleAttempt,
      assertions: {
        conflict_friendly: conflictFriendly,
        stale_blocked: staleBlocked,
        no_raw_trace: noRawTrace,
      },
    });

    await pageA.getByRole('button', { name: /^放弃$/ }).click();
    await waitForFormReady(pageA);
    await waitForFieldValueByLabel(pageA, '名称', secondTabName);
    const afterDiscardValue = normalize(await fieldValueByLabel(pageA, '名称'));
    const feedbackAfterDiscard = await visibleFeedback(pageA);

    await fillFieldByLabel(pageA, '名称', recoveredName);
    await saveForm(pageA);
    await waitForSaveSuccess(pageA);
    const afterRecoverySave = await readDictionary(pageA, createdId);
    const recoveredPersisted = normalize(afterRecoverySave?.name) === recoveredName;
    const recoveredFromLatest = afterDiscardValue === secondTabName;
    const conflictCleared = !/数据已被其他操作更新|RECORD_VERSION_CONFLICT/.test(feedbackAfterDiscard);
    summary.checks.push({
      path_id: 'P24',
      name: 'stale form can discard, reload latest value, and save again',
      status: recoveredFromLatest && conflictCleared && recoveredPersisted ? 'pass' : 'fail',
      after_discard_value: afterDiscardValue,
      feedback_after_discard: feedbackAfterDiscard,
      after_recovery_save: afterRecoverySave,
      expected_latest_before_retry: secondTabName,
      recovered_name: recoveredName,
      assertions: {
        recovered_from_latest: recoveredFromLatest,
        conflict_cleared: conflictCleared,
        recovered_persisted: recoveredPersisted,
      },
    });

    summary.console_errors = {
      first_tab: pageA.__consoleErrors || [],
      second_tab: pageB.__consoleErrors || [],
    };
  } finally {
    summary.fixture_cleanup = await cleanup(pageA, code).catch((err) => ({
      code,
      errors: [err instanceof Error ? err.message : String(err)],
    }));
    await pageA.screenshot({ path: path.join(outDir, 'first_tab_final.png'), fullPage: true }).catch(() => {});
    await pageB.screenshot({ path: path.join(outDir, 'second_tab_final.png'), fullPage: true }).catch(() => {});
    await contextA.close().catch(() => {});
    await contextB.close().catch(() => {});
    await browser.close().catch(() => {});
  }

  summary.actionable_console_errors = actionableConsoleErrors(summary);
  summary.pass = summary.checks.every((check) => check.status === 'pass')
    && summary.actionable_console_errors.length === 0
    && !summary.fixture_cleanup?.errors?.length;
  writeJson('summary.json', summary);
  console.log(`[form_concurrency_conflict_acceptance] artifacts=${outDir}`);
  console.log(JSON.stringify({
    pass: summary.pass,
    checks: summary.checks.map((check) => ({ name: check.name, status: check.status })),
    fixture_id: summary.fixture_id,
    fixture_code: summary.fixture_code,
    cleanup: summary.fixture_cleanup,
    actionable_console_errors: summary.actionable_console_errors.length,
  }, null, 2));
  if (!summary.pass) process.exit(1);
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[form_concurrency_conflict_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
