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
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const LONG_DECIMAL_CELL_RE = /^-?\d{1,3}(?:,\d{3})*(?:\.\d{3,}|\d*\.\d{3,})$/;

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
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    return text.includes('公司经营情况表')
      && text.includes('年-月份')
      && text.includes('2026年-5月')
      && text.includes('营收')
      && text.includes('收入合计')
      && text.includes('支出合计')
      && !text.includes('未匹配公司')
      && !text.includes('正在加载列表')
      && !text.includes('当前视图使用可读降级渲染');
  }, { timeout: 90000 });
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

async function openFromMenu(page) {
  const statsGroup = page.locator('button.label', { hasText: '统计分析' });
  await statsGroup.click();
  const reportEntry = page.locator('button.label', { hasText: '公司经营情况表' });
  await reportEntry.waitFor({ state: 'visible', timeout: 15000 });
  await reportEntry.click();
  await page.waitForFunction((actionId) => {
    return window.location.pathname === `/a/${actionId}`;
  }, ACTION_ID, { timeout: 30000 });
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
    artifacts: outDir,
    errors: [],
  };
  const context = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
  const page = await context.newPage();
  attachConsoleCapture(page);
  try {
    await login(page);
    await openFromMenu(page);
    await waitForActionReady(page);
    const action = await snapshot(page, 'company_operation_summary');
    requireIncludes(action.text, '公司经营情况表', 'report_title', result.errors);
    requireIncludes(action.text, '年-月份', 'period_header', result.errors);
    requireIncludes(action.text, '2026年-5月', 'period_row', result.errors);
    requireIncludes(action.text, '营收', 'revenue_header', result.errors);
    requireIncludes(action.text, '收入合计', 'income_header', result.errors);
    requireIncludes(action.text, '支出合计', 'expense_header', result.errors);
    requireIncludes(action.text, '扣款实缴登记/管理费', 'deduction_management_fee_header', result.errors);
    requireIncludes(action.text, '财务收入/标书制作费', 'bid_document_fee_income_header', result.errors);
    requireIncludes(action.text, '报销申请/报销', 'reimbursement_header', result.errors);
    if (action.text.includes('未匹配公司')) {
      result.errors.push({ label: 'unmatched_company_should_not_show', expected: 'no 未匹配公司' });
    }
    const numericCellTexts = await page.evaluate(() => Array.from(
      document.querySelectorAll('td, th, .summary-value, .footer-number-value'),
    )
      .map((el) => String(el.textContent || '').replace(/\s+/g, ' ').trim())
      .filter(Boolean));
    const longDecimalCells = numericCellTexts.filter((text) => LONG_DECIMAL_CELL_RE.test(text));
    if (longDecimalCells.length) {
      result.errors.push({
        label: 'amount_decimal_places',
        expected: 'numeric cells keep at most 2 decimals',
        actual: longDecimalCells.slice(0, 10),
      });
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
