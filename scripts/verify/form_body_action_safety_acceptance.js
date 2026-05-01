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
const MODEL = process.env.MVP_MODEL || 'project.project';
const RECORD_ID = process.env.RECORD_ID || '771';
const ACTION_ID = process.env.ACTION_ID || '506';
const MENU_ID = process.env.MENU_ID || '353';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-body-action-safety', ts);

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

function unwrapContract(payload) {
  if (!payload || typeof payload !== 'object') return {};
  if (payload.result && typeof payload.result === 'object') return payload.result;
  if (payload.data && typeof payload.data === 'object') return payload.data;
  return payload;
}

function collectLayoutButtons(nodes, out = []) {
  for (const node of Array.isArray(nodes) ? nodes : []) {
    if (!node || typeof node !== 'object') continue;
    if (String(node.type || '').trim().toLowerCase() === 'button') {
      out.push({
        name: normalize(node.name),
        label: normalize(node.label || node.string || node.name),
        buttonType: normalize(node.buttonType),
        action: node.action || {},
      });
    }
    for (const key of ['children', 'pages', 'tabs', 'nodes', 'items']) {
      if (Array.isArray(node[key])) collectLayoutButtons(node[key], out);
    }
  }
  return out;
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

async function openFormAndCaptureContract(page) {
  const contractPromise = new Promise((resolve) => {
    page.on('response', async (response) => {
      try {
        if (!response.url().includes('/api/v1/intent')) return;
        const request = response.request();
        const rawPost = request.postData() || '';
        if (!rawPost.includes('"ui.contract"')) return;
        const payload = await response.json();
        resolve(unwrapContract(payload));
      } catch {
        // Ignore unrelated responses.
      }
    });
  });
  await page.goto(`${FRONTEND_URL}/r/${MODEL}/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    return !text.includes('正在加载页面') && !text.includes('页面加载失败') && !text.includes('页面渲染失败');
  }, null, { timeout: 30000 });
  return Promise.race([
    contractPromise,
    page.waitForTimeout(12000).then(() => ({})),
  ]);
}

async function openBoqTab(page) {
  await page.locator('button.native-tab').filter({ hasText: /^工程量清单$/ }).first().click();
  await page.locator('.native-tab-panel button.native-action-btn').filter({ hasText: /^工程量清单分析$/ }).first().waitFor({ timeout: 15000 });
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const result = {
    db: DB_NAME,
    login: LOGIN,
    model: MODEL,
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    frontend_url: FRONTEND_URL,
    artifact_dir: outDir,
    checks: [],
  };
  let context;
  try {
    context = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
    const page = await context.newPage();
    attachConsoleCapture(page);
    const executeRequests = [];
    page.on('request', (request) => {
      const body = request.postData() || '';
      if (request.url().includes('/api/v1/intent') && body.includes('"execute_button"')) {
        executeRequests.push(body);
      }
    });
    await login(page);
    const contract = await openFormAndCaptureContract(page);
    const buttons = collectLayoutButtons(contract?.views?.form?.layout || []);
    result.contract_buttons = buttons.map((row) => ({
      label: row.label,
      name: row.name,
      kind: row.action?.kind,
      safety: row.action?.action_safety || null,
    }));

    const safeButton = buttons.find((row) => row.label === '工程量清单分析');
    const dangerButton = buttons.find((row) => row.label === '重建工程量清单层级');
    const safeSafety = safeButton?.action?.action_safety || {};
    const dangerSafety = dangerButton?.action?.action_safety || {};
    result.checks.push({
      path_id: 'P19',
      name: 'body action contract declares safe navigation classification',
      status: safeButton
        && safeButton.action?.kind === 'open'
        && safeSafety.classification === 'safe'
        && safeSafety.requires_confirm === false
        ? 'pass'
        : 'fail',
      safe_button: safeButton || null,
    });
    result.checks.push({
      path_id: 'P19',
      name: 'body action contract declares dangerous mutation guard',
      status: dangerButton
        && dangerButton.action?.kind === 'object'
        && dangerSafety.classification === 'danger'
        && dangerSafety.requires_confirm === true
        && normalize(dangerSafety.confirm_message)
        ? 'pass'
        : 'fail',
      danger_button: dangerButton || null,
    });

    await openBoqTab(page);
    const beforeUrl = page.url();
    const dialogs = [];
    page.once('dialog', async (dialog) => {
      dialogs.push({ type: dialog.type(), message: dialog.message() });
      await dialog.dismiss();
    });
    await page.locator('.native-tab-panel button.native-action-btn').filter({ hasText: /^重建工程量清单层级$/ }).first().click();
    await page.waitForTimeout(1200);
    result.checks.push({
      path_id: 'P19',
      name: 'dangerous body action is guarded and dismiss prevents execute_button',
      status: dialogs.length === 1
        && dialogs[0].message.includes('重建工程量清单层级')
        && executeRequests.length === 0
        && page.url() === beforeUrl
        ? 'pass'
        : 'fail',
      dialogs,
      execute_request_count_after_dismiss: executeRequests.length,
      before_url: beforeUrl,
      after_url: page.url(),
    });

    await page.locator('.native-tab-panel button.native-action-btn').filter({ hasText: /^工程量清单分析$/ }).first().click();
    await page.waitForURL((url) => url.href !== beforeUrl, { timeout: 15000 });
    result.checks.push({
      path_id: 'P19',
      name: 'safe body action still navigates without confirm',
      status: page.url() !== beforeUrl ? 'pass' : 'fail',
      before_url: beforeUrl,
      after_url: page.url(),
    });

    await page.screenshot({ path: path.join(outDir, 'custom_p19_body_actions.png'), fullPage: true });
    result.console_errors = page.__consoleErrors || [];
    result.pass = result.checks.every((row) => row.status === 'pass') && result.console_errors.length === 0;
    writeJson('summary.json', result);
    console.log(`[form_body_action_safety_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: result.pass,
      checks: result.checks.map((row) => ({ name: row.name, status: row.status })),
      console_errors: result.console_errors.length,
    }, null, 2));
    if (!result.pass) process.exit(1);
  } finally {
    if (context) await context.close();
    await browser.close();
  }
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[form_body_action_safety_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
