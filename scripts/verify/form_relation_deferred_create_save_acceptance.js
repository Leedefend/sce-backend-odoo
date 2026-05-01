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
const RECORD_ID = Number(process.env.RECORD_ID || 771);
const ACTION_ID = Number(process.env.ACTION_ID || 506);
const MENU_ID = Number(process.env.MENU_ID || 353);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-relation-deferred-create-save', ts);

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
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 });
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
        'X-Trace-Id': `form-relation-deferred-${Date.now()}`,
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
    };
  }, {
    dbName: DB_NAME,
    authToken,
    intentName: intent,
    payload: params,
    allowError: Boolean(options.allowError),
  });
}

async function listPartnerByName(page, label) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'list',
    model: 'res.partner',
    fields: ['id', 'name', 'display_name'],
    domain: [['name', '=', label]],
    limit: 5,
    context: {},
  });
  return Array.isArray(resp.data.records) ? resp.data.records : [];
}

async function readProject(page) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'project.project',
    ids: [RECORD_ID],
    fields: ['id', 'name', 'partner_id'],
    context: {},
  });
  const row = Array.isArray(resp.data.records) ? resp.data.records[0] : null;
  if (!row) throw new Error(`project.project/${RECORD_ID} not found`);
  return row;
}

async function restoreProjectPartner(page, originalPartnerId) {
  return intentRequest(page, 'api.data', {
    op: 'write',
    model: 'project.project',
    ids: [RECORD_ID],
    vals: { partner_id: originalPartnerId || false },
    context: {},
  }, { allowError: true });
}

async function unlinkPartner(page, partnerId) {
  if (!partnerId) return { ok: true, status: 0, data: { skipped: true }, error: {} };
  return intentRequest(page, 'api.data.unlink', {
    model: 'res.partner',
    ids: [partnerId],
    context: {},
  }, { allowError: true });
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
  await page.goto(`${FRONTEND_URL}/r/project.project/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
}

function customerInput(page) {
  return page.locator('.many2one-combobox').nth(0).locator('input');
}

async function saveForm(page) {
  await page.locator('.template-page-header-actions button.primary').filter({ hasText: /^保存$/ }).first().click();
  await page.getByText('保存成功，已同步最新表单内容。', { exact: true }).waitFor({ timeout: 20000 });
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, locale: 'zh-CN' });
  attachConsoleCapture(page);

  const label = `P09 Deferred Partner ${Date.now()}`;
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: 'project.project',
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    artifact_dir: outDir,
    label,
    checks: [],
    cleanup: {},
  };
  let originalPartnerId = 0;
  let createdPartnerId = 0;

  try {
    await login(page);
    const beforeProject = await readProject(page);
    originalPartnerId = Array.isArray(beforeProject.partner_id) ? Number(beforeProject.partner_id[0] || 0) : 0;
    const beforeRows = await listPartnerByName(page, label);

    await openProject(page);
    await customerInput(page).fill(label);
    await customerInput(page).blur();
    await page.waitForTimeout(1400);
    const inlineLabels = await page.locator('.many2one-inline-create').allInnerTexts().catch(() => []);
    const rowsAfterInput = await listPartnerByName(page, label);
    const saveButtonsAfterInput = await page.locator('.template-page-header-actions button').evaluateAll((nodes) => nodes.map((node) => ({
      text: String(node.textContent || '').replace(/\s+/g, ' ').trim(),
      disabled: Boolean(node.disabled),
    })));

    await saveForm(page);
    const rowsAfterSave = await listPartnerByName(page, label);
    createdPartnerId = Number(rowsAfterSave[0]?.id || 0);
    const afterSaveProject = await readProject(page);
    const afterPartnerId = Array.isArray(afterSaveProject.partner_id) ? Number(afterSaveProject.partner_id[0] || 0) : 0;

    summary.checks.push({
      path_id: 'P09',
      level: 'L4',
      scenario: 'deferred_many2one_create_on_main_save',
      status: beforeRows.length === 0
        && rowsAfterInput.length === 0
        && inlineLabels.some((text) => normalize(text).includes(label))
        && saveButtonsAfterInput.some((button) => button.text === '保存' && !button.disabled)
        && rowsAfterSave.length === 1
        && createdPartnerId > 0
        && afterPartnerId === createdPartnerId
        ? 'pass'
        : 'fail',
      original_partner_id: originalPartnerId,
      before_rows: beforeRows,
      inline_labels: inlineLabels.map(normalize),
      rows_after_input: rowsAfterInput,
      save_buttons_after_input: saveButtonsAfterInput,
      rows_after_save: rowsAfterSave,
      after_project_partner_id: afterSaveProject.partner_id,
      created_partner_id: createdPartnerId,
    });
  } catch (err) {
    summary.error = err instanceof Error ? err.stack || err.message : String(err);
  } finally {
    if (originalPartnerId || createdPartnerId) {
      summary.cleanup.restore_project_partner = await restoreProjectPartner(page, originalPartnerId).catch((err) => ({
        ok: false,
        error: { message: err instanceof Error ? err.message : String(err) },
      }));
    }
    if (createdPartnerId) {
      summary.cleanup.unlink_partner = await unlinkPartner(page, createdPartnerId).catch((err) => ({
        ok: false,
        error: { message: err instanceof Error ? err.message : String(err) },
      }));
      summary.cleanup.remaining_partners = await listPartnerByName(page, label).catch((err) => ([
        { error: err instanceof Error ? err.message : String(err) },
      ]));
      summary.cleanup.project_after_cleanup = await readProject(page).catch((err) => ({
        error: err instanceof Error ? err.message : String(err),
      }));
    }
    summary.actionable_console_errors = (page.__consoleErrors || []).filter((line) =>
      !String(line).includes('favicon') && !String(line).includes('ResizeObserver'),
    );
    summary.pass = !summary.error
      && summary.checks.every((item) => item.status === 'pass')
      && summary.actionable_console_errors.length === 0
      && summary.cleanup.restore_project_partner?.ok !== false
      && summary.cleanup.unlink_partner?.ok !== false
      && Array.isArray(summary.cleanup.remaining_partners)
      && summary.cleanup.remaining_partners.length === 0;
    await page.screenshot({ path: path.join(outDir, summary.pass ? 'final.png' : 'failure.png'), fullPage: true }).catch(() => {});
    writeJson('summary.json', summary);
    await browser.close();
  }

  if (!summary.pass) {
    console.error(JSON.stringify(summary, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify(summary, null, 2));
}

main();
