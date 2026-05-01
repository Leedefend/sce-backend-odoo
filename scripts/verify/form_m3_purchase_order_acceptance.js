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
const SUBMITTER_LOGIN = process.env.SUBMITTER_LOGIN || 'caisiqi';
const SUBMITTER_PASSWORD = process.env.SUBMITTER_PASSWORD || '123456';
const RECORD_ID = Number(process.env.PURCHASE_ORDER_ID || 0);
const ACTION_ID = Number(process.env.ACTION_ID || 549);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-m3-purchase-order', ts);

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
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

async function login(page, loginName, password) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(loginName);
  await inputs.nth(1).fill(password);
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
        'X-Trace-Id': `form-m3-purchase-${Date.now()}`,
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

async function openPurchaseForm(page) {
  await page.goto(`${FRONTEND_URL}/r/purchase.order/${RECORD_ID}?action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function pageFacts(page) {
  return page.evaluate(() => {
    const text = (node) => String(node?.textContent || '').replace(/\s+/g, ' ').trim();
    return {
      url: window.location.href,
      buttons: Array.from(document.querySelectorAll('.template-layout-shell button')).map(text).filter(Boolean),
      statusbar: Array.from(document.querySelectorAll('.native-statusbar-step')).map((node) => ({
        label: text(node),
        active: node.classList.contains('native-statusbar-step--active'),
      })),
      visible_error: text(document.querySelector('.status-panel.error, .validation-error')),
      text_sample: text(document.querySelector('.template-layout-shell')).slice(0, 900),
    };
  });
}

async function readOrder(page) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'purchase.order',
    ids: [RECORD_ID],
    fields: ['id', 'name', 'state', 'validation_status', 'reject_reason'],
  });
  const record = Array.isArray(resp.data?.records) ? resp.data.records[0] || {} : {};
  return { resp, record };
}

async function main() {
  if (!RECORD_ID) {
    throw new Error('PURCHASE_ORDER_ID is required');
  }
  const browser = await chromium.launch({ headless: true });
  const submitterPage = await browser.newPage({ viewport: { width: 1440, height: 980 } });
  attachConsoleCapture(submitterPage);

  const summary = {
    pass: false,
    db: DB_NAME,
    model: 'purchase.order',
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    artifact_dir: outDir,
    checks: [],
  };

  try {
    await login(submitterPage, SUBMITTER_LOGIN, SUBMITTER_PASSWORD);
    await openPurchaseForm(submitterPage);
    const beforeFacts = await pageFacts(submitterPage);
    summary.checks.push({
      path_id: 'M3-P30',
      name: 'purchase rfq form renders object confirm action',
      status: beforeFacts.buttons.some((item) => item === '确认订单')
        && !beforeFacts.buttons.some((item) => item === '审批通过' || item === '审批驳回')
        && !beforeFacts.visible_error
        ? 'pass'
        : 'fail',
      dom: beforeFacts,
    });

    await submitterPage.getByRole('button', { name: /^确认订单$/ }).first().click();
    await submitterPage.waitForTimeout(2500);
    const afterSubmit = await readOrder(submitterPage);
    const submitState = normalize(afterSubmit.record.state);
    const submitValidation = normalize(afterSubmit.record.validation_status);
    summary.checks.push({
      path_id: 'M3-P30',
      name: 'submitter confirms rfq according to current non-blocking approval policy',
      status: afterSubmit.resp.ok
        && ['purchase', 'done'].includes(submitState)
        && ['no', 'validated', ''].includes(submitValidation)
        ? 'pass'
        : 'fail',
      record: afterSubmit.record,
    });

    await openPurchaseForm(submitterPage);
    const afterFacts = await pageFacts(submitterPage);
    summary.checks.push({
      path_id: 'M3-P31',
      name: 'non-pending approval actions stay hidden after confirm',
      status: !afterFacts.buttons.some((item) => item === '审批通过' || item === '审批驳回')
        && !afterFacts.visible_error
        ? 'pass'
        : 'fail',
      dom: afterFacts,
    });

    const consoleErrors = [...(submitterPage.__consoleErrors || [])];
    summary.console_errors = consoleErrors;
    summary.unexpected_console_errors = consoleErrors;
    summary.pass = summary.checks.every((row) => row.status === 'pass') && consoleErrors.length === 0;
    writeJson('summary.json', summary);
  } finally {
    await browser.close();
  }

  console.log(JSON.stringify(summary, null, 2));
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
