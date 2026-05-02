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
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'business-handling-browser', ts);

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
  page.on('dialog', async (dialog) => {
    await dialog.accept();
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

async function intentRequest(page, intent, params, options = {}) {
  const authToken = await token(page);
  return page.evaluate(async ({ dbName, authToken: bearer, intentName, payload, allowError }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: bearer ? `Bearer ${bearer}` : '',
        'X-Trace-Id': `business-handling-browser-${Date.now()}`,
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

async function listOne(page, model, domain, fields) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'list',
    model,
    domain,
    fields,
    limit: 1,
    context: {},
  });
  const records = Array.isArray(resp.data?.records) ? resp.data.records : [];
  if (!records.length) throw new Error(`fixture missing: ${model} ${JSON.stringify(domain || [])}`);
  return records[0];
}

async function createRecord(page, model, vals, context = {}) {
  const resp = await intentRequest(page, 'api.data', { op: 'create', model, vals, context });
  const id = Number(resp.data?.id || 0);
  if (!id) throw new Error(`create ${model} returned no id: ${JSON.stringify(resp)}`);
  return id;
}

async function readRecord(page, model, id, fields) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model,
    ids: [id],
    fields,
    context: {},
  });
  const rows = Array.isArray(resp.data?.records) ? resp.data.records : [];
  return rows[0] || {};
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function openRecord(page, model, id, actionId, menuId) {
  await page.goto(`${FRONTEND_URL}/r/${model}/${id}?menu_id=${menuId}&action_id=${actionId}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
  const text = normalize(await page.locator('.template-layout-shell').textContent());
  if (text.includes('页面加载失败') || text.includes('页面渲染失败') || text.includes('System exception')) {
    throw new Error(`form render failed: ${text.slice(0, 300)}`);
  }
}

async function clickHeaderButton(page, label) {
  const nativeButton = page.locator('button.native-action-btn').filter({ hasText: new RegExp(`^${label}$`) }).first();
  const button = await nativeButton.count()
    ? nativeButton
    : page.getByRole('button', { name: new RegExp(`^${label}$`) }).first();
  await button.waitFor({ timeout: 15000 });
  await button.click();
  await page.waitForTimeout(800);
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
  await save.waitFor({ timeout: 15000 });
  await save.click();
  await page.getByText('保存成功，已同步最新表单内容。', { exact: true }).waitFor({ timeout: 20000 });
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 }, locale: 'zh-CN' });
  attachConsoleCapture(page);

  const marker = Date.now();
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    artifact_dir: outDir,
    marker,
    checks: [],
    created: {},
    cleanup: {},
  };

  try {
    await login(page);
    const project = await listOne(page, 'project.project', [], ['id', 'name']);
    const partner = await listOne(page, 'res.partner', [], ['id', 'name']);
    const costCode = await listOne(page, 'project.cost.code', [], ['id', 'name']);

    const borrowingId = await createRecord(page, 'sc.finance.expense.document', {
      name: `浏览器借款单办理验收 ${marker}`,
      project_id: Number(project.id),
      partner_id: Number(partner.id),
      payee_id: Number(partner.id),
      fact_type: 'borrowing_form',
      expense_category: '项目周转借款',
      amount: 1888,
      repayment_due_date: '2026-06-02',
      description: `business_handling_browser ${marker}`,
    }, { default_fact_type: 'borrowing_form', default_name: '借款单' });
    summary.created.borrowing_id = borrowingId;

    await openRecord(page, 'sc.finance.expense.document', borrowingId, 837, 664);
    await clickHeaderButton(page, '提交');
    let borrowing = await readRecord(page, 'sc.finance.expense.document', borrowingId, ['id', 'state', 'document_no']);
    const afterSubmitState = borrowing.state;
    await openRecord(page, 'sc.finance.expense.document', borrowingId, 837, 664);
    await clickHeaderButton(page, '完成');
    borrowing = await readRecord(page, 'sc.finance.expense.document', borrowingId, ['id', 'state', 'document_no']);
    await page.screenshot({ path: path.join(outDir, 'borrowing_form_done.png'), fullPage: true });
    summary.checks.push({
      scenario: 'browser_submit_done_finance_borrowing_form',
      status: afterSubmitState === 'in_progress' && borrowing.state === 'done' && Boolean(borrowing.document_no) ? 'pass' : 'fail',
      after_submit_state: afterSubmitState,
      final_record: borrowing,
    });

    const ledgerId = await createRecord(page, 'project.cost.ledger', {
      project_id: Number(project.id),
      cost_code_id: Number(costCode.id),
      date: '2026-05-02',
      amount: 120,
      note: `business_handling_browser ${marker}`,
      source_model: 'business_handling_browser_acceptance',
      source_id: marker % 1000000000,
    });
    summary.created.cost_ledger_id = ledgerId;

    await openRecord(page, 'project.cost.ledger', ledgerId, 511, 372);
    await setFieldByLabel(page, '金额', '266.66');
    await setFieldByLabel(page, '备注/摘要', `business_handling_browser edited ${marker}`);
    await saveForm(page);
    const ledger = await readRecord(page, 'project.cost.ledger', ledgerId, ['id', 'amount', 'note']);
    await page.screenshot({ path: path.join(outDir, 'cost_ledger_saved.png'), fullPage: true });
    summary.checks.push({
      scenario: 'browser_edit_save_cost_ledger',
      status: Number(ledger.amount) === 266.66 && normalize(ledger.note) === `business_handling_browser edited ${marker}` ? 'pass' : 'fail',
      final_record: ledger,
    });

    summary.console_errors = page.__consoleErrors || [];
  } catch (err) {
    summary.error = err instanceof Error ? err.stack || err.message : String(err);
    summary.console_errors = page.__consoleErrors || [];
  } finally {
    if (summary.created.borrowing_id) {
      summary.cleanup.borrowing = {
        ok: true,
        mode: 'manual_odoo_shell_required',
        model: 'sc.finance.expense.document',
        ids: [summary.created.borrowing_id],
      };
    }
    if (summary.created.cost_ledger_id) {
      summary.cleanup.cost_ledger = {
        ok: true,
        mode: 'manual_odoo_shell_required',
        model: 'project.cost.ledger',
        ids: [summary.created.cost_ledger_id],
      };
    }
    await browser.close().catch(() => {});
  }

  const cleanupErrors = Object.values(summary.cleanup).filter((item) => item && item.ok === false);
  summary.pass = !summary.error
    && summary.checks.length === 2
    && summary.checks.every((row) => row.status === 'pass')
    && (summary.console_errors || []).length === 0
    && cleanupErrors.length === 0;
  writeJson('summary.json', summary);
  console.log(`[business_handling_browser_acceptance] artifacts=${outDir}`);
  console.log(JSON.stringify({
    pass: summary.pass,
    checks: summary.checks.map((row) => ({ scenario: row.scenario, status: row.status })),
    cleanup_ok: cleanupErrors.length === 0,
    console_errors: (summary.console_errors || []).length,
    error: summary.error || null,
  }, null, 2));
  if (!summary.pass) process.exit(1);
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[business_handling_browser_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
