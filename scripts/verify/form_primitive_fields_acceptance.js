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
const PROJECT_ACTION_ID = Number(process.env.PROJECT_ACTION_ID || 506);
const PROJECT_RECORD_ID = Number(process.env.PROJECT_RECORD_ID || 771);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-primitive-fields', ts);

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
        'X-Trace-Id': `form-primitive-fields-${Date.now()}`,
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

async function openProjectRecord(page) {
  await page.goto(`${FRONTEND_URL}/r/project.project/${PROJECT_RECORD_ID}?action_id=${PROJECT_ACTION_ID}&menu_id=353`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
}

async function fieldSurface(page) {
  return page.evaluate(() => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return Array.from(document.querySelectorAll('.field')).map((field) => {
      const label = clean(field.querySelector('.label')?.textContent || '').replace(/\*$/, '');
      const input = field.querySelector('input.input, input.input-checkbox, textarea.input, select.input');
      const options = input?.tagName === 'SELECT'
        ? Array.from(input.querySelectorAll('option')).map((option) => ({ value: option.value, text: clean(option.textContent) }))
        : [];
      return {
        label,
        tag: input?.tagName?.toLowerCase() || '',
        type: input?.getAttribute('type') || '',
        value: input?.tagName === 'INPUT' && input.getAttribute('type') === 'checkbox'
          ? Boolean(input.checked)
          : input?.value || '',
        disabled: Boolean(input?.disabled),
        options,
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
}

async function waitForSaveSuccess(page) {
  await page.getByText('保存成功，已同步最新表单内容。', { exact: true }).waitFor({ timeout: 15000 });
}

async function listDictionary(page, code) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'list',
    model: 'sc.dictionary',
    fields: ['id', 'name', 'code', 'type', 'sequence', 'active', 'display_name'],
    domain: [['code', '=', code]],
    limit: 20,
    context: {},
  });
  if (!resp.ok) throw new Error(`list sc.dictionary failed: ${JSON.stringify(resp.error || resp.data)}`);
  return Array.isArray(resp.data?.records) ? resp.data.records : [];
}

async function readDictionary(page, id) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'sc.dictionary',
    ids: [id],
    fields: ['id', 'name', 'code', 'type', 'sequence', 'active', 'display_name'],
    context: {},
  });
  if (!resp.ok) throw new Error(`read sc.dictionary failed: ${JSON.stringify(resp.error || resp.data)}`);
  const rows = Array.isArray(resp.data?.records) ? resp.data.records : [];
  return rows[0] || null;
}

async function readProjectFavorite(page) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'project.project',
    ids: [PROJECT_RECORD_ID],
    fields: ['id', 'name', 'is_favorite'],
    context: {},
  });
  if (!resp.ok) throw new Error(`read project.project failed: ${JSON.stringify(resp.error || resp.data)}`);
  const rows = Array.isArray(resp.data?.records) ? resp.data.records : [];
  return rows[0] || null;
}

async function clickFavoriteToggle(page) {
  const button = page.locator('.field-favorite-toggle').first();
  await button.waitFor({ timeout: 15000 });
  if (await button.isDisabled().catch(() => true)) {
    throw new Error('favorite boolean toggle is disabled');
  }
  await button.click();
  await page.waitForTimeout(800);
}

async function waitForDictionaryRows(page, code, predicate, timeoutMs = 20000) {
  const deadline = Date.now() + timeoutMs;
  let rows = [];
  while (Date.now() < deadline) {
    rows = await listDictionary(page, code);
    if (predicate(rows)) return rows;
    await page.waitForTimeout(500);
  }
  return rows;
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
  const resp = await intentRequest(page, 'api.data.unlink', { model: 'sc.dictionary', ids, context: {} });
  result.public_unlink_ok = resp.ok === true;
  if (!resp.ok && normalize(resp.error?.reason_code || resp.error?.code) === 'DELETE_POLICY_DENIED') {
    result.public_unlink_denied = true;
    result.requires_shell_cleanup = true;
  } else if (!resp.ok) {
    result.errors.push(JSON.stringify(resp.error || resp.data));
  }
  return result;
}

function actionableConsoleErrors(summary) {
  const errors = Array.isArray(summary.console_errors) ? summary.console_errors : [];
  const expectedDeletePolicyDenied = summary.fixture_cleanup?.public_unlink_denied === true
    && summary.fixture_cleanup?.requires_shell_cleanup === true;
  if (!expectedDeletePolicyDenied) return errors;
  return errors.filter((text) => !String(text || '').includes('403 (FORBIDDEN)'));
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
  attachConsoleCapture(page);

  const unique = Date.now();
  const code = `P06PRIM${unique}`;
  const name = `P06 primitive ${unique}`;
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

  try {
    await login(page);
    await cleanup(page, code);
    await openCreate(page);
    const createSurface = await fieldSurface(page);
    summary.create_surface = createSurface;
    const byLabel = Object.fromEntries(createSurface.map((row) => [row.label, row]));
    const contract = await intentRequest(page, 'ui.contract', {
      op: 'action_open',
      action_id: ACTION_ID,
      render_profile: 'create',
      contract_surface: 'user',
    });
    summary.contract_field_types = Object.fromEntries(
      ['name', 'code', 'type', 'sequence', 'active'].map((field) => [
        field,
        contract.data?.fields?.[field]?.type || contract.data?.fields?.[field]?.ttype || '',
      ]),
    );
    summary.checks.push({
      path_id: 'P06',
      name: 'primitive controls use contract-backed widgets for char, integer, selection, boolean',
      status: byLabel['名称']?.tag === 'input'
        && byLabel['编码']?.tag === 'input'
        && byLabel['排序']?.type === 'number'
        && byLabel['字典类型']?.tag === 'select'
        && byLabel['字典类型']?.options?.some((option) => option.value === 'project_type' && option.text === '项目类型')
        ? 'pass'
        : 'fail',
      controls: {
        name: byLabel['名称'],
        code: byLabel['编码'],
        sequence: byLabel['排序'],
        type: byLabel['字典类型'],
      },
      contract_field_types: summary.contract_field_types,
    });

    await setFieldByLabel(page, '名称', name);
    await setFieldByLabel(page, '编码', code);
    await setFieldByLabel(page, '字典类型', 'project_type');
    await setFieldByLabel(page, '排序', 123);
    await saveForm(page);
    const createdRows = await waitForDictionaryRows(page, code, (rows) => rows.length === 1);
    const createdId = Number(createdRows[0]?.id || 0);
    summary.fixture_id = createdId;
    summary.checks.push({
      path_id: 'P06/P23',
      name: 'primitive values create and persist with expected backend types',
      status: createdRows.length === 1
        && normalize(createdRows[0].name) === name
        && normalize(createdRows[0].code) === code
        && normalize(createdRows[0].type) === 'project_type'
        && Number(createdRows[0].sequence) === 123
        ? 'pass'
        : 'fail',
      rows: createdRows,
    });

    await openRecord(page, createdId);
    const editSurfaceBefore = await fieldSurface(page);
    await setFieldByLabel(page, '名称', editedName);
    await setFieldByLabel(page, '字典类型', 'cost_item');
    await setFieldByLabel(page, '排序', 456);
    await saveForm(page);
    await waitForSaveSuccess(page);
    const afterEdit = await readDictionary(page, createdId);
    await openRecord(page, createdId);
    const editSurfaceAfter = await fieldSurface(page);
    summary.checks.push({
      path_id: 'P06/P04/P23',
      name: 'primitive values edit, reload, and display with saved values',
      status: normalize(afterEdit?.name) === editedName
        && normalize(afterEdit?.type) === 'cost_item'
        && Number(afterEdit?.sequence) === 456
        && editSurfaceAfter.some((row) => row.label === '名称' && row.value === editedName)
        && editSurfaceAfter.some((row) => row.label === '排序' && Number(row.value) === 456)
        && editSurfaceAfter.some((row) => row.label === '字典类型' && row.value === 'cost_item')
        ? 'pass'
        : 'fail',
      before: editSurfaceBefore,
      after_edit: afterEdit,
      after_reload_surface: editSurfaceAfter,
    });

    const projectBefore = await readProjectFavorite(page);
    await openProjectRecord(page);
    const favoriteBefore = await page.evaluate(() => {
      const btn = document.querySelector('.field-favorite-toggle');
      return {
        present: Boolean(btn),
        aria_pressed: btn?.getAttribute('aria-pressed') || '',
        label: btn?.getAttribute('aria-label') || '',
        disabled: Boolean(btn?.disabled),
      };
    });
    await clickFavoriteToggle(page);
    const projectAfterToggle = await readProjectFavorite(page);
    await clickFavoriteToggle(page);
    const projectAfterRestore = await readProjectFavorite(page);
    summary.checks.push({
      path_id: 'P06/P23',
      name: 'boolean favorite widget toggles, persists, and restores without frontend business inference',
      status: favoriteBefore.present
        && favoriteBefore.label === '在仪表板上显示项目'
        && favoriteBefore.disabled === false
        && projectAfterToggle?.is_favorite === !Boolean(projectBefore?.is_favorite)
        && projectAfterRestore?.is_favorite === Boolean(projectBefore?.is_favorite)
        ? 'pass'
        : 'fail',
      project_id: PROJECT_RECORD_ID,
      favorite_before_surface: favoriteBefore,
      project_before: projectBefore,
      project_after_toggle: projectAfterToggle,
      project_after_restore: projectAfterRestore,
    });

    await page.screenshot({ path: path.join(outDir, 'primitive_fields_final.png'), fullPage: true });
    summary.console_errors = page.__consoleErrors || [];
  } finally {
    summary.fixture_cleanup = await cleanup(page, code).catch((err) => ({
      code,
      errors: [err instanceof Error ? err.message : String(err)],
    }));
    await browser.close().catch(() => {});
  }

  summary.actionable_console_errors = actionableConsoleErrors(summary);
  summary.pass = summary.checks.every((check) => check.status === 'pass')
    && summary.actionable_console_errors.length === 0
    && !summary.fixture_cleanup?.errors?.length;
  writeJson('summary.json', summary);
  console.log(`[form_primitive_fields_acceptance] artifacts=${outDir}`);
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
  console.error(`[form_primitive_fields_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
