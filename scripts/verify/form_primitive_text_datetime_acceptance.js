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
const ACTION_ID = Number(process.env.ACTION_ID || 610);
const PROJECT_ID = Number(process.env.PROJECT_ID || 514);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-primitive-text-datetime', ts);

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
        'X-Trace-Id': `form-primitive-text-datetime-${Date.now()}`,
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

async function createDiary(page, marker) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'create',
    model: 'sc.construction.diary',
    vals: {
      project_id: PROJECT_ID,
      date_diary: '2099-11-10 08:20:00',
      document_no: `P06C-${marker}`,
      title: `P06C primitive text datetime ${marker}`,
      description: `P06C initial description ${marker}`,
      header_description: `P06C initial header ${marker}`,
      note: `P06C initial note ${marker}`,
      source_origin: 'manual',
    },
    context: {},
  });
  if (!resp.ok || !Number(resp.data?.id)) {
    throw new Error(`create sc.construction.diary failed: ${JSON.stringify(resp.error || resp.data)}`);
  }
  return Number(resp.data.id);
}

async function readDiary(page, id) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'sc.construction.diary',
    ids: [id],
    fields: ['id', 'date_diary', 'document_no', 'title', 'description', 'header_description', 'note', 'source_origin', 'state'],
    context: {},
  });
  if (!resp.ok) throw new Error(`read sc.construction.diary failed: ${JSON.stringify(resp.error || resp.data)}`);
  return Array.isArray(resp.data?.records) ? resp.data.records[0] || null : null;
}

async function listDiaries(page, marker) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'list',
    model: 'sc.construction.diary',
    domain: [['document_no', '=', `P06C-${marker}`]],
    fields: ['id'],
    limit: 20,
    context: {},
  });
  if (!resp.ok) return [];
  return Array.isArray(resp.data?.records) ? resp.data.records : [];
}

async function unlinkPublic(page, ids) {
  if (!ids.length) return { skipped: true, ids: [] };
  return intentRequest(page, 'api.data.unlink', { model: 'sc.construction.diary', ids, context: {} });
}

async function cleanup(page, marker) {
  const rows = await listDiaries(page, marker).catch(() => []);
  const ids = rows.map((row) => Number(row.id)).filter(Boolean);
  const result = {
    marker,
    diary_ids: ids,
    public_unlink_denied: false,
    requires_shell_cleanup: false,
    errors: [],
  };
  const resp = await unlinkPublic(page, ids).catch((err) => ({
    ok: false,
    error: { message: err instanceof Error ? err.message : String(err) },
  }));
  if (ids.length && !resp.ok) {
    result.public_unlink_denied = true;
    result.requires_shell_cleanup = true;
    const code = normalize(resp.error?.reason_code || resp.error?.code || resp.error?.message);
    if (code && code !== 'DELETE_POLICY_DENIED') result.errors.push(code);
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

async function openDiary(page, id) {
  await page.goto(`${FRONTEND_URL}/r/sc.construction.diary/${id}?action_id=${ACTION_ID}`, {
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
    const input = target.querySelector('input.input, textarea.input, select.input');
    if (!input) return false;
    input.value = String(fieldValue);
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
  const editedDescription = `P06C edited description line 1 ${marker}\nP06C edited description line 2`;
  const editedHeader = `P06C edited header ${marker}\ncontract text field`;
  const editedNote = `P06C edited note ${marker}`;
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: 'sc.construction.diary',
    action_id: ACTION_ID,
    artifact_dir: outDir,
    marker,
    checks: [],
  };

  try {
    await login(page);
    await cleanup(page, marker);
    const diaryId = await createDiary(page, marker);
    summary.fixture_ids = { diary_id: diaryId };

    await openDiary(page, diaryId);
    const surface = await fieldSurface(page);
    const byLabel = Object.fromEntries(surface.map((row) => [row.label, row]));
    summary.checks.push({
      path_id: 'P06',
      name: 'datetime and text controls render from contract-backed field types',
      status: byLabel['日志日期']?.type === 'datetime-local'
        && byLabel['日志内容']?.tag === 'textarea'
        && byLabel['单据说明']?.tag === 'textarea'
        && byLabel['备注']?.tag === 'textarea'
        ? 'pass'
        : 'fail',
      surface,
    });

    await setFieldByLabel(page, '日志日期', '2099-11-12T09:35');
    await setFieldByLabel(page, '日志内容', editedDescription);
    await setFieldByLabel(page, '单据说明', editedHeader);
    await setFieldByLabel(page, '备注', editedNote);
    await saveForm(page);
    const afterEdit = await readDiary(page, diaryId);
    await openDiary(page, diaryId);
    const afterReloadSurface = await fieldSurface(page);
    summary.checks.push({
      path_id: 'P06/P04/P23',
      name: 'datetime and text values edit, persist, and reload',
      status: normalize(afterEdit?.date_diary) === '2099-11-12 09:35:00'
        && normalize(afterEdit?.description) === normalize(editedDescription)
        && normalize(afterEdit?.header_description) === normalize(editedHeader)
        && normalize(afterEdit?.note) === normalize(editedNote)
        && afterReloadSurface.some((row) => row.label === '日志日期' && row.value === '2099-11-12T09:35')
        && afterReloadSurface.some((row) => row.label === '日志内容' && normalize(row.value) === normalize(editedDescription))
        && afterReloadSurface.some((row) => row.label === '单据说明' && normalize(row.value) === normalize(editedHeader))
        && afterReloadSurface.some((row) => row.label === '备注' && normalize(row.value) === normalize(editedNote))
        ? 'pass'
        : 'fail',
      after_edit: afterEdit,
      after_reload_surface: afterReloadSurface,
    });

    summary.console_errors = page.__consoleErrors || [];
    await page.screenshot({ path: path.join(outDir, 'text_datetime_final.png'), fullPage: true });
  } finally {
    summary.fixture_cleanup = await cleanup(page, marker).catch((err) => ({
      marker,
      errors: [err instanceof Error ? err.message : String(err)],
    }));
    await browser.close().catch(() => {});
  }

  summary.actionable_console_errors = actionableConsoleErrors(summary);
  summary.pass = summary.checks.every((check) => check.status === 'pass')
    && summary.actionable_console_errors.length === 0
    && !summary.fixture_cleanup?.errors?.length;
  writeJson('summary.json', summary);
  console.log(`[form_primitive_text_datetime_acceptance] artifacts=${outDir}`);
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
  console.error(`[form_primitive_text_datetime_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
