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
const ACTION_ID = Number(process.env.ACTION_ID || 506);
const MENU_ID = Number(process.env.MENU_ID || 353);
const PROJECT_RECORD_ID = Number(process.env.PROJECT_RECORD_ID || 771);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-primitive-html', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function htmlContains(value, expected) {
  return normalize(value).includes(normalize(expected));
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
        'X-Trace-Id': `form-primitive-html-${Date.now()}`,
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

async function readProject(page) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'project.project',
    ids: [PROJECT_RECORD_ID],
    fields: ['id', 'name', 'description'],
    context: {},
  });
  if (!resp.ok) throw new Error(`read project.project failed: ${JSON.stringify(resp.error || resp.data)}`);
  return Array.isArray(resp.data?.records) ? resp.data.records[0] || null : null;
}

async function writeProjectDescription(page, description) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'write',
    model: 'project.project',
    ids: [PROJECT_RECORD_ID],
    vals: { description },
    context: {},
  });
  if (!resp.ok) throw new Error(`restore project.project description failed: ${JSON.stringify(resp.error || resp.data)}`);
  return resp;
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function openProject(page) {
  await page.goto(`${FRONTEND_URL}/r/project.project/${PROJECT_RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
}

async function openDescriptionTab(page) {
  const tab = page.locator('.native-tab').filter({ hasText: /^描述$/ }).first();
  await tab.waitFor({ timeout: 15000 });
  await tab.click();
  await page.waitForFunction(() => {
    const labels = Array.from(document.querySelectorAll('.field .label'))
      .map((item) => String(item.textContent || '').replace(/\s+/g, ' ').trim().replace(/\*$/, ''));
    return labels.includes('描述') || labels.includes('说明');
  }, null, { timeout: 15000 });
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

function pickDescriptionField(surface) {
  const candidates = surface.filter((row) => row.tag === 'textarea');
  return candidates.find((row) => ['描述', '说明'].includes(row.label))
    || candidates.find((row) => row.label.includes('描述') || row.label.includes('说明'))
    || null;
}

async function setFieldByLabel(page, label, value) {
  const ok = await page.evaluate(({ labelText, fieldValue }) => {
    const clean = (val) => String(val || '').replace(/\s+/g, ' ').trim();
    const fields = Array.from(document.querySelectorAll('.field'));
    const target = fields.find((field) => clean(field.querySelector('.label')?.textContent || '').replace(/\*$/, '') === labelText);
    if (!target) return false;
    const input = target.querySelector('textarea.input, input.input, select.input');
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
  const editedHtml = `<p>P06D edited project html ${marker}</p><ol><li>line A</li><li><strong>line B</strong></li></ol>`;
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: 'project.project',
    record_id: PROJECT_RECORD_ID,
    action_id: ACTION_ID,
    artifact_dir: outDir,
    marker,
    checks: [],
  };
  let originalDescription = null;
  let restoreResult = null;

  try {
    await login(page);
    const before = await readProject(page);
    originalDescription = String(before?.description || '');
    summary.before = before;

    await openProject(page);
    await openDescriptionTab(page);
    const surface = await fieldSurface(page);
    const descriptionField = pickDescriptionField(surface);
    summary.checks.push({
      path_id: 'P06',
      name: 'html control renders from contract-backed field type',
      status: descriptionField?.tag === 'textarea' ? 'pass' : 'fail',
      description_field: descriptionField,
      textarea_labels: surface.filter((row) => row.tag === 'textarea').map((row) => row.label),
    });
    if (!descriptionField) throw new Error('project.project html description textarea not found');

    await setFieldByLabel(page, descriptionField.label, editedHtml);
    await saveForm(page);
    const afterEdit = await readProject(page);
    await openProject(page);
    await openDescriptionTab(page);
    const afterReloadSurface = await fieldSurface(page);
    const afterReloadDescription = pickDescriptionField(afterReloadSurface);
    summary.checks.push({
      path_id: 'P06/P04/P23',
      name: 'html value edits, persists, and reloads',
      status: htmlContains(afterEdit?.description, `P06D edited project html ${marker}`)
        && htmlContains(afterEdit?.description, '<strong>line B</strong>')
        && afterReloadDescription?.tag === 'textarea'
        && htmlContains(afterReloadDescription.value, `P06D edited project html ${marker}`)
        && htmlContains(afterReloadDescription.value, '<strong>line B</strong>')
        ? 'pass'
        : 'fail',
      after_edit: afterEdit,
      after_reload_description: afterReloadDescription,
    });

    summary.console_errors = page.__consoleErrors || [];
    await page.screenshot({ path: path.join(outDir, 'html_final.png'), fullPage: true });
  } finally {
    if (originalDescription !== null) {
      restoreResult = await writeProjectDescription(page, originalDescription).catch((err) => ({
        ok: false,
        error: err instanceof Error ? err.message : String(err),
      }));
    }
    summary.restore = restoreResult || { skipped: true, reason: 'original description was not captured' };
    summary.after_restore = await readProject(page).catch((err) => ({
      error: err instanceof Error ? err.message : String(err),
    }));
    await browser.close().catch(() => {});
  }

  summary.actionable_console_errors = Array.isArray(summary.console_errors) ? summary.console_errors : [];
  summary.pass = summary.checks.every((check) => check.status === 'pass')
    && summary.actionable_console_errors.length === 0
    && (summary.restore?.ok === true || summary.restore?.skipped === true)
    && normalize(summary.after_restore?.description) === normalize(originalDescription);
  writeJson('summary.json', summary);
  console.log(`[form_primitive_html_acceptance] artifacts=${outDir}`);
  console.log(JSON.stringify({
    pass: summary.pass,
    checks: summary.checks.map((check) => ({ name: check.name, status: check.status })),
    restore: summary.restore,
    restored: normalize(summary.after_restore?.description) === normalize(originalDescription),
    actionable_console_errors: summary.actionable_console_errors.length,
  }, null, 2));
  if (!summary.pass) process.exit(1);
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[form_primitive_html_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
