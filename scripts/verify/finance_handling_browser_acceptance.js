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

const ROOT_DIR = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? process.cwd()
  : path.resolve(process.cwd(), '../../..');
const FRONTEND_URL = process.env.FRONTEND_URL || process.env.E2E_BASE_URL || 'http://localhost:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.join(ROOT_DIR, 'artifacts');
const OUT_DIR = process.env.FINANCE_BROWSER_ARTIFACT_DIR
  || path.join(ARTIFACTS_DIR, 'finance-browser-handling', 'current');
const SETUP_JSON = path.join(OUT_DIR, 'setup.json');
const HEADLESS = String(process.env.HEADLESS || '1').trim() !== '0';
const CHROMIUM_EXECUTABLE_PATH = process.env.CHROMIUM_EXECUTABLE_PATH
  || process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
  || '';

function ensureDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function writeJson(name, data) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(path.join(OUT_DIR, name), JSON.stringify(data, null, 2) + '\n', 'utf8');
}

function writeMarkdown(report) {
  const lines = [
    '# Finance Handling Browser Acceptance',
    '',
    `- ok: ${report.ok}`,
    `- frontend_url: ${report.frontend_url}`,
    `- db_name: ${report.db_name}`,
    `- login: ${report.login}`,
    `- company: ${report.company}`,
    `- currency: ${report.currency}`,
    '',
    '| case | model | record | expected_state | final_state | ledger_count | screenshots | errors |',
    '| --- | --- | ---: | --- | --- | ---: | ---: | ---: |',
  ];
  for (const row of report.rows) {
    lines.push(
      `| ${row.label} | ${row.model} | ${row.record_id} | ${row.expected_state} | ${row.final_state || ''} | ${row.ledger_count ?? ''} | ${row.screenshots.length} | ${row.errors.length} |`,
    );
  }
  fs.writeFileSync(path.join(OUT_DIR, 'summary.md'), lines.join('\n') + '\n', 'utf8');
}

function attachPageGuards(page) {
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

async function login(page, setup) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}&t=${Date.now()}`, {
    waitUntil: 'networkidle',
    timeout: 45000,
  });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(setup.login);
  await inputs.nth(1).fill(setup.password);
  const dbInput = inputs.nth(2);
  const dbEditable = await dbInput.isEditable().catch(() => false);
  if (dbEditable) {
    await dbInput.fill(DB_NAME);
  } else {
    const currentDb = normalize(await dbInput.inputValue().catch(() => ''));
    if (currentDb && currentDb !== DB_NAME) {
      throw new Error(`login db input is locked to ${currentDb}, expected ${DB_NAME}`);
    }
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 30000 });
  await page.waitForLoadState('networkidle').catch(() => {});
}

async function authToken(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intentRequest(page, intent, params) {
  const token = await authToken(page);
  return page.evaluate(async ({ dbName, bearer, intentName, payload }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: bearer ? `Bearer ${bearer}` : '',
        'X-Trace-Id': `finance-handling-browser-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params: payload }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || body.ok === false) {
      throw new Error(body?.error?.message || body?.message || `${intentName} failed`);
    }
    return body.data || {};
  }, { dbName: DB_NAME, bearer: token, intentName: intent, payload: params });
}

async function readRecord(page, model, id, fields) {
  const data = await intentRequest(page, 'api.data', {
    op: 'read',
    model,
    ids: [id],
    fields,
    context: {},
  });
  const rows = Array.isArray(data.records) ? data.records : [];
  return rows[0] || {};
}

async function ledgerCount(page, ledgerModel, paymentRequestId) {
  if (!ledgerModel || !paymentRequestId) return 0;
  const data = await intentRequest(page, 'api.data', {
    op: 'list',
    model: ledgerModel,
    domain: [['payment_request_id', '=', paymentRequestId]],
    fields: ['id', 'payment_request_id'],
    limit: 10,
    context: {},
  });
  return Array.isArray(data.records) ? data.records.length : 0;
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败') || text.includes('System exception')) return true;
    return !text.includes('正在加载页面') && !text.includes('正在加载场景');
  }, null, { timeout: 30000 }).catch(() => {});
  const text = normalize(await page.locator('.template-layout-shell').textContent().catch(() => ''));
  if (text.includes('页面加载失败') || text.includes('页面渲染失败') || text.includes('System exception')) {
    throw new Error(`record render failed: ${text.slice(0, 500)}`);
  }
  return text;
}

function recordUrl(row) {
  const params = new URLSearchParams();
  if (row.menu?.menu_id) params.set('menu_id', String(row.menu.menu_id));
  if (row.menu?.action_id) params.set('action_id', String(row.menu.action_id));
  const suffix = params.toString() ? `?${params.toString()}` : '';
  return `${FRONTEND_URL}/r/${row.model}/${row.record_id}${suffix}`;
}

async function screenshot(page, row, suffix) {
  const safeKey = row.key.replace(/[^a-z0-9_-]+/gi, '_');
  const fileName = `${safeKey}_${suffix}.png`;
  const filePath = path.join(OUT_DIR, fileName);
  await page.screenshot({ path: filePath, fullPage: true });
  return fileName;
}

async function clickAction(page, label, options = {}) {
  const exact = new RegExp(`^\\s*${label}\\s*$`);
  const button = page.locator('button.native-action-btn, button').filter({ hasText: exact }).first();
  const count = await button.count();
  if (!count) {
    if (options.optional) return false;
    throw new Error(`action button not found: ${label}`);
  }
  await button.waitFor({ state: 'visible', timeout: options.timeout || 18000 });
  await button.click();
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(options.pause || 900);
  const text = normalize(await page.locator('.template-layout-shell').textContent().catch(() => ''));
  if (/页面加载失败|页面渲染失败|System exception|操作失败|权限不足|Access Denied|Traceback/i.test(text)) {
    throw new Error(`action ${label} failed: ${text.slice(0, 600)}`);
  }
  return true;
}

async function runCase(page, row) {
  const result = {
    key: row.key,
    label: row.label,
    model: row.model,
    record_id: row.record_id,
    expected_state: row.expected_state,
    final_state: '',
    payment_request_id: false,
    ledger_model: row.ledger_model || '',
    ledger_count: 0,
    screenshots: [],
    steps: [],
    errors: [],
  };
  try {
    await page.goto(recordUrl(row), { waitUntil: 'domcontentloaded', timeout: 45000 });
    const text = await waitForFormReady(page);
    if (!text.includes(row.label) && !text.includes(row.display_name) && !text.includes('办理')) {
      throw new Error(`record page lacks business label: ${row.label}`);
    }
    result.screenshots.push(await screenshot(page, row, 'before'));

    for (const step of row.steps) {
      const optional = step === '审批通过';
      const clicked = await clickAction(page, step, { optional });
      result.steps.push({ label: step, clicked });
      if (clicked) {
        result.screenshots.push(await screenshot(page, row, `after_${result.steps.length}`));
      }
    }

    const fields = ['id', 'state'];
    if (row.model !== 'payment.request') fields.push('payment_request_id');
    const record = await readRecord(page, row.model, row.record_id, fields);
    result.final_state = record.state || '';
    if (row.model === 'payment.request') {
      result.payment_request_id = row.record_id;
    } else if (Array.isArray(record.payment_request_id)) {
      result.payment_request_id = record.payment_request_id[0] || false;
    } else {
      result.payment_request_id = Number(record.payment_request_id || 0) || false;
    }
    result.ledger_count = await ledgerCount(page, row.ledger_model, result.payment_request_id);
    if (result.final_state !== row.expected_state) {
      throw new Error(`expected ${row.expected_state}, got ${result.final_state}`);
    }
    if (row.ledger_model && result.ledger_count < 1) {
      throw new Error(`expected downstream ledger in ${row.ledger_model}`);
    }
  } catch (err) {
    result.errors.push(err instanceof Error ? err.stack || err.message : String(err));
    try {
      result.screenshots.push(await screenshot(page, row, 'error'));
    } catch {
      // keep original error
    }
  }
  return result;
}

async function main() {
  ensureDir(SETUP_JSON);
  const setup = JSON.parse(fs.readFileSync(SETUP_JSON, 'utf8'));
  if (CHROMIUM_EXECUTABLE_PATH && !fs.existsSync(CHROMIUM_EXECUTABLE_PATH)) {
    throw new Error(`configured browser executable does not exist: ${CHROMIUM_EXECUTABLE_PATH}`);
  }
  const launchOptions = { headless: HEADLESS };
  if (CHROMIUM_EXECUTABLE_PATH) {
    launchOptions.executablePath = CHROMIUM_EXECUTABLE_PATH;
  }
  const browser = await chromium.launch(launchOptions);
  const context = await browser.newContext({ viewport: { width: 1440, height: 1100 }, locale: 'zh-CN' });
  const page = await context.newPage();
  attachPageGuards(page);

  const report = {
    ok: false,
    frontend_url: FRONTEND_URL,
    db_name: DB_NAME,
    login: setup.login,
    company: setup.company,
    currency: setup.currency,
    artifact_dir: OUT_DIR,
    rows: [],
    console_errors: [],
  };

  try {
    await login(page, setup);
    for (const row of setup.cases || []) {
      report.rows.push(await runCase(page, row));
    }
    report.console_errors = page.__consoleErrors || [];
  } catch (err) {
    report.error = err instanceof Error ? err.stack || err.message : String(err);
    report.console_errors = page.__consoleErrors || [];
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }

  report.ok = !report.error
    && report.rows.length === 5
    && report.rows.every((row) => row.errors.length === 0)
    && report.console_errors.length === 0;

  writeJson('summary.json', report);
  writeMarkdown(report);
  console.log(`[finance_handling_browser_acceptance] artifacts=${OUT_DIR}`);
  console.log(JSON.stringify({
    ok: report.ok,
    rows: report.rows.map((row) => ({
      key: row.key,
      final_state: row.final_state,
      ledger_count: row.ledger_count,
      errors: row.errors.length,
    })),
    console_errors: report.console_errors.length,
    error: report.error || null,
  }, null, 2));
  if (!report.ok) process.exit(1);
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[finance_handling_browser_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
