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
const outDir = path.join(ARTIFACTS_DIR, 'form-edit-discard', ts);

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

async function intentRequest(page, intent, params) {
  const authToken = await token(page);
  return page.evaluate(async ({ dbName, authToken: bearer, intentName, payload }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: bearer ? `Bearer ${bearer}` : '',
        'X-Trace-Id': `form-edit-discard-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params: payload }),
    });
    const body = await response.json().catch(() => ({}));
    return {
      status: response.status,
      ok: body.ok === true,
      data: body.data || {},
      error: body.error || {},
    };
  }, { dbName: DB_NAME, authToken, intentName: intent, payload: params });
}

async function readProjectName(page) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'project.project',
    ids: [RECORD_ID],
    fields: ['id', 'name'],
    context: {},
  });
  if (!resp.ok) throw new Error(`read project failed: ${JSON.stringify(resp.error || resp.data)}`);
  const record = Array.isArray(resp.data?.records) ? resp.data.records[0] : null;
  return String(record?.name || '');
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

async function fieldInputByLabel(page, label) {
  const locator = page.locator('.field').filter({ has: page.locator('.label', { hasText: new RegExp(`^${label}\\*?$`) }) }).first();
  await locator.waitFor({ timeout: 15000 });
  return locator.locator('input.input, textarea.input, select.input').first();
}

async function visibleHeaderButtons(page) {
  return page.locator('.template-page-header-actions button').evaluateAll((nodes) => nodes.map((node) => ({
    text: String(node.textContent || '').replace(/\s+/g, ' ').trim(),
    disabled: Boolean(node.disabled),
  })));
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: 'zh-CN' });
  attachConsoleCapture(page);

  const marker = `P04 discard should not persist ${Date.now()}`;
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: 'project.project',
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    artifact_dir: outDir,
    checks: [],
  };

  try {
    await login(page);
    const beforeName = await readProjectName(page);
    await openProject(page);
    const input = await fieldInputByLabel(page, '名称');
    const initialInputValue = await input.inputValue();
    await input.fill(marker);
    await page.getByRole('button', { name: /^放弃$/ }).waitFor({ timeout: 10000 });
    const buttonsAfterEdit = await visibleHeaderButtons(page);
    await page.getByRole('button', { name: /^放弃$/ }).click();
    await waitForFormReady(page);
    const afterDiscardInput = await (await fieldInputByLabel(page, '名称')).inputValue();
    const afterName = await readProjectName(page);
    const buttonsAfterDiscard = await visibleHeaderButtons(page);

    summary.checks.push({
      path_id: 'P04',
      level: 'L4',
      scenario: 'discard_unsaved_main_field_change',
      status: beforeName === initialInputValue
        && afterDiscardInput === beforeName
        && afterName === beforeName
        && buttonsAfterEdit.some((button) => button.text === '放弃' && !button.disabled)
        && !buttonsAfterDiscard.some((button) => button.text === '放弃')
        ? 'pass'
        : 'fail',
      before_name: beforeName,
      initial_input_value: initialInputValue,
      edited_value: marker,
      after_discard_input: afterDiscardInput,
      after_db_name: afterName,
      buttons_after_edit: buttonsAfterEdit,
      buttons_after_discard: buttonsAfterDiscard,
    });
    summary.actionable_console_errors = page.__consoleErrors.filter((line) =>
      !String(line).includes('favicon') && !String(line).includes('ResizeObserver'),
    );
    summary.pass = summary.checks.every((item) => item.status === 'pass')
      && summary.actionable_console_errors.length === 0;
    await page.screenshot({ path: path.join(outDir, 'project-after-discard.png'), fullPage: true });
  } catch (err) {
    summary.error = err instanceof Error ? err.stack || err.message : String(err);
    summary.actionable_console_errors = page.__consoleErrors || [];
    await page.screenshot({ path: path.join(outDir, 'failure.png'), fullPage: true }).catch(() => {});
  } finally {
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
