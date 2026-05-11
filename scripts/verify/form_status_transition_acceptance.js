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
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const PROJECT_PREFIX = process.env.PROJECT_PREFIX || 'P15 Status Acceptance';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-status-transition', ts);

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
  const dbInput = inputs.nth(2);
  if (await dbInput.count().catch(() => 0)) {
    const disabled = await dbInput.isDisabled().catch(() => false);
    if (!disabled) await dbInput.fill(DB_NAME);
  }
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
        'X-Trace-Id': `form-status-transition-${Date.now()}`,
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
      meta: body.meta || {},
    };
  }, {
    dbName: DB_NAME,
    authToken,
    intentName: intent,
    payload: params,
    allowError: Boolean(options.allowError),
  });
}

async function createProject(page, name) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'create',
    model: 'project.project',
    vals: {
      name,
      location: 'P15 acceptance temporary location',
    },
    context: {},
  });
  const id = Number(resp.data.id || 0);
  if (!id) throw new Error(`project create returned no id: ${JSON.stringify(resp)}`);
  return id;
}

async function readProject(page, id) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'project.project',
    ids: [id],
    fields: ['id', 'name', 'lifecycle_state'],
    context: {},
  });
  const row = Array.isArray(resp.data.records) ? resp.data.records[0] || {} : {};
  return { resp, row };
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function openProject(page, id) {
  await page.goto(`${FRONTEND_URL}/r/project.project/${id}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
}

async function statusbarSnapshot(page) {
  return page.locator('.native-statusbar-step').evaluateAll((nodes) => nodes.map((node) => ({
    label: String(node.textContent || '').replace(/\s+/g, ' ').trim(),
    active: node.classList.contains('native-statusbar-step--active'),
    disabled: node.hasAttribute('disabled'),
  })));
}

async function saveForm(page) {
  await page.locator('.template-page-header-actions button.primary').filter({ hasText: /^保存$/ }).first().click();
  await page.waitForTimeout(600);
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, locale: 'zh-CN' });
  attachConsoleCapture(page);

  const projectName = `${PROJECT_PREFIX} ${Date.now()}`;
  const summary = {
    db: DB_NAME,
    login: LOGIN,
    model: 'project.project',
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    artifact_dir: outDir,
    project_name: projectName,
    project_id: 0,
    checks: [],
  };

  try {
    await login(page);
    summary.project_id = await createProject(page, projectName);
    const beforeRead = await readProject(page, summary.project_id);
    await openProject(page, summary.project_id);
    const beforeStatusbar = await statusbarSnapshot(page);
    const target = page.locator('.native-statusbar-step').filter({ hasText: /^停工$/ }).first();
    await target.waitFor({ timeout: 15000 });
    const targetDisabled = await target.isDisabled();
    await target.click();
    const afterClickStatusbar = await statusbarSnapshot(page);
    await saveForm(page);
    await openProject(page, summary.project_id);
    const afterSaveStatusbar = await statusbarSnapshot(page);
    const afterRead = await readProject(page, summary.project_id);
    summary.checks.push({
      path_id: 'P15',
      level: 'L4',
      scenario: 'statusbar_safe_transition_draft_to_paused',
      status: beforeRead.row.lifecycle_state === 'draft'
        && targetDisabled === false
        && afterClickStatusbar.some((row) => row.label === '停工' && row.active)
        ? 'pass'
        : 'fail',
      before_record: beforeRead.row,
      after_record: afterRead.row,
      target_disabled: targetDisabled,
      before_statusbar: beforeStatusbar,
      after_click_statusbar: afterClickStatusbar,
      after_save_statusbar: afterSaveStatusbar,
    });
    summary.console_errors = page.__consoleErrors || [];
    await page.screenshot({ path: path.join(outDir, 'paused_project_form.png'), fullPage: true });
    summary.pass = summary.checks.every((row) => row.status === 'pass') && summary.console_errors.length === 0;
    writeJson('summary.json', summary);
    console.log(`[form_status_transition_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: summary.pass,
      project_id: summary.project_id,
      checks: summary.checks.map((row) => ({ scenario: row.scenario, status: row.status })),
      console_errors: summary.console_errors.length,
    }, null, 2));
    process.exit(summary.pass ? 0 : 1);
  } catch (err) {
    summary.pass = false;
    summary.error = err instanceof Error ? err.stack || err.message : String(err);
    summary.console_errors = page.__consoleErrors || [];
    writeJson('summary.json', summary);
    console.error(`[form_status_transition_acceptance] failed artifacts=${outDir}`);
    console.error(summary.error);
    process.exit(1);
  } finally {
    await browser.close().catch(() => {});
  }
}

main();
