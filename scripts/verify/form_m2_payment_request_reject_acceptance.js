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
const APPROVER_LOGIN = process.env.APPROVER_LOGIN || 'chenshuai';
const APPROVER_PASSWORD = process.env.APPROVER_PASSWORD || '123456';
const RECORD_ID = Number(process.env.PAYMENT_REQUEST_ID || 28489);
const ACTION_ID = Number(process.env.ACTION_ID || 585);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const REJECT_REASON = process.env.REJECT_REASON || `M2 reject acceptance ${new Date().toISOString()}`;

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-m2-payment-request-reject', ts);

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
        'X-Trace-Id': `form-m2-payment-reject-${Date.now()}`,
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

function collectBusinessActions(contract) {
  const form = contract?.views?.form || {};
  const rows = Array.isArray(form.business_actions) ? form.business_actions : [];
  return rows.map((row) => ({
    key: normalize(row.key),
    action_key: normalize(row.action_key),
    label: normalize(row.label),
    allowed: row.allowed === true,
    reason_code: normalize(row.reason_code),
    requires_reason: row.requires_reason === true,
    required_params: Array.isArray(row.required_params) ? row.required_params.map(normalize).filter(Boolean) : [],
    has_mutation: Boolean(row.mutation && typeof row.mutation === 'object'),
  }));
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
      text_sample: text(document.querySelector('.template-layout-shell')).slice(0, 800),
    };
  });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const financePage = await browser.newPage({ viewport: { width: 1440, height: 980 } });
  const approverPage = await browser.newPage({ viewport: { width: 1440, height: 980 } });
  attachConsoleCapture(financePage);
  attachConsoleCapture(approverPage);

  const summary = {
    pass: false,
    db: DB_NAME,
    model: 'payment.request',
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    artifact_dir: outDir,
    reject_reason: REJECT_REASON,
    checks: [],
  };

  try {
    await login(financePage, LOGIN, PASSWORD);
    const submitResp = await intentRequest(financePage, 'payment.request.execute', {
      id: RECORD_ID,
      action: 'submit',
    });
    summary.checks.push({
      path_id: 'M2-P23',
      name: 'finance submits request before reject path',
      status: submitResp.ok && submitResp.status === 200 && normalize(submitResp.data?.payment_request?.state) === 'submit' ? 'pass' : 'fail',
      execute: {
        status: submitResp.status,
        ok: submitResp.ok,
        payment_request_state: normalize(submitResp.data?.payment_request?.state),
        reason_code: normalize(submitResp.error.reason_code || submitResp.data.reason_code),
      },
    });

    await login(approverPage, APPROVER_LOGIN, APPROVER_PASSWORD);
    const contractResp = await intentRequest(approverPage, 'ui.contract', {
      action_id: ACTION_ID,
      record_id: RECORD_ID,
      render_profile: 'edit',
    });
    const actions = collectBusinessActions(contractResp.data);
    const rejectAction = actions.find((row) => row.action_key === 'reject') || {};
    summary.checks.push({
      path_id: 'M2-P23',
      name: 'reject action declares required reason contract',
      status: contractResp.ok
        && rejectAction.allowed === true
        && rejectAction.reason_code === 'OK'
        && rejectAction.requires_reason === true
        && Array.isArray(rejectAction.required_params)
        && rejectAction.required_params.includes('reason')
        && rejectAction.has_mutation === true
        ? 'pass'
        : 'fail',
      reject_action: rejectAction,
    });

    await approverPage.goto(`${FRONTEND_URL}/r/payment.request/${RECORD_ID}?action_id=${ACTION_ID}`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    });
    await approverPage.locator('.template-layout-shell').waitFor({ timeout: 30000 });
    await approverPage.waitForFunction(() => {
      const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
      if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
      return !text.includes('正在加载页面');
    }, null, { timeout: 30000 });
    const beforeFacts = await pageFacts(approverPage);
    summary.checks.push({
      path_id: 'M2-P23',
      name: 'approver form renders reject button',
      status: beforeFacts.buttons.some((text) => text === '驳回') ? 'pass' : 'fail',
      dom: beforeFacts,
    });

    approverPage.once('dialog', async (dialog) => {
      summary.dialog = {
        type: dialog.type(),
        message: dialog.message(),
      };
      await dialog.accept(REJECT_REASON);
    });
    await approverPage.getByRole('button', { name: /^驳回$/ }).first().click();
    await approverPage.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);
    await approverPage.waitForTimeout(1200);

    const verifyResp = await intentRequest(approverPage, 'api.data', {
      op: 'read',
      model: 'payment.request',
      ids: [RECORD_ID],
      fields: ['id', 'state', 'validation_status'],
    });
    const record = Array.isArray(verifyResp.data?.records) ? verifyResp.data.records[0] || {} : {};
    const state = normalize(record.state);
    const afterFacts = await pageFacts(approverPage);
    summary.checks.push({
      path_id: 'M2-P23',
      name: 'reject button submits reason and moves request to rejected',
      status: verifyResp.ok && state === 'rejected' && normalize(summary.dialog?.message).includes('原因') ? 'pass' : 'fail',
      verify: {
        status: verifyResp.status,
        ok: verifyResp.ok,
        state,
        dialog: summary.dialog || {},
      },
      dom: afterFacts,
    });

    const consoleErrors = [...(financePage.__consoleErrors || []), ...(approverPage.__consoleErrors || [])];
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
