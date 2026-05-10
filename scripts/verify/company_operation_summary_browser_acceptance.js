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

const FRONTEND_URL = process.env.FRONTEND_URL || process.env.E2E_BASE_URL || 'http://localhost:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_acceptance_audit_20260510';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ACTION_ID = process.env.ACTION_ID || '821';
const MENU_ID = process.env.MENU_ID || '626';
const EXPECTED_COMPANY = process.env.EXPECTED_COMPANY || '四川保盛建设集团有限公司';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'company-operation-summary-browser-acceptance', ts);

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

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}&t=${Date.now()}`, {
    waitUntil: 'networkidle',
    timeout: 45000,
  });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  if (await inputs.count() >= 3) {
    await inputs.nth(2).fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 30000 });
}

async function waitForActionReady(page) {
  await page.locator('.template-layout-shell, .page').first().waitFor({ timeout: 30000 });
  await page.waitForFunction((expectedCompany) => {
    const text = String(document.body?.textContent || '');
    return text.includes('公司经营情况表')
      && text.includes(expectedCompany)
      && text.includes('收入合计')
      && text.includes('支出合计')
      && text.includes('经营净额')
      && !text.includes('未匹配公司')
      && !text.includes('正在加载列表')
      && !text.includes('当前视图使用可读降级渲染');
  }, EXPECTED_COMPANY, { timeout: 90000 });
}

async function snapshot(page, name) {
  const data = await page.evaluate(() => ({
    url: window.location.href,
    title: String(document.querySelector('h1')?.textContent || document.title).replace(/\s+/g, ' ').trim(),
    text: String(document.body?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 6000),
  }));
  await page.screenshot({ path: path.join(outDir, `${name}.png`), fullPage: true });
  writeJson(`${name}.json`, data);
  return data;
}

function requireIncludes(text, needle, label, errors) {
  if (!String(text || '').includes(needle)) {
    errors.push({ label, expected: needle });
  }
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const result = {
    frontend_url: FRONTEND_URL,
    db: DB_NAME,
    login: LOGIN,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    expected_company: EXPECTED_COMPANY,
    artifacts: outDir,
    errors: [],
  };
  const context = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
  const page = await context.newPage();
  attachConsoleCapture(page);
  try {
    await login(page);
    await page.goto(`${FRONTEND_URL}/a/${ACTION_ID}?menu_id=${MENU_ID}`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    });
    await waitForActionReady(page);
    const action = await snapshot(page, 'company_operation_summary');
    requireIncludes(action.text, '公司经营情况表', 'report_title', result.errors);
    requireIncludes(action.text, EXPECTED_COMPANY, 'company_row', result.errors);
    requireIncludes(action.text, '收入合计', 'income_header', result.errors);
    requireIncludes(action.text, '支出合计', 'expense_header', result.errors);
    requireIncludes(action.text, '经营净额', 'net_header', result.errors);
    if (action.text.includes('未匹配公司')) {
      result.errors.push({ label: 'unmatched_company_should_not_show', expected: 'no 未匹配公司' });
    }
    result.console_errors = page.__consoleErrors || [];
    result.pass = result.errors.length === 0 && result.console_errors.length === 0;
    writeJson('summary.json', result);
    console.log(`[company_operation_summary_browser_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({ pass: result.pass, errors: result.errors, console_errors: result.console_errors }, null, 2));
    if (!result.pass) process.exit(1);
  } finally {
    await context.close();
    await browser.close();
  }
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[company_operation_summary_browser_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
