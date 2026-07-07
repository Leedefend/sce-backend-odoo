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
const ACTION_ID = process.env.ACTION_ID || '506';
const MENU_ID = process.env.MENU_ID || '367';
const RECORD_ID = process.env.RECORD_ID || '2';
const EXPECTED_PROJECT_CODE = process.env.EXPECTED_PROJECT_CODE || 'STJ-MYHSTLDCDPZGC-255';
const EXPECTED_LEGACY_PROJECT_ID = process.env.EXPECTED_LEGACY_PROJECT_ID || '00c73f013e234461883beac337e8d75d';
const EXPECTED_COMPANY = process.env.EXPECTED_COMPANY || '四川保盛建设集团有限公司';
const EXPECTED_CREATED_AT = process.env.EXPECTED_CREATED_AT || '03/31/2020 14:42:08';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'project-legacy-fact-browser-acceptance', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function clean(value) {
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

async function waitForPageReady(page) {
  await page.locator('.template-layout-shell, .page').first().waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    return !text.includes('正在加载页面') && !text.includes('正在加载列表') && !text.includes('页面加载失败');
  }, null, { timeout: 30000 });
}

async function snapshot(page, name) {
  const data = await page.evaluate(() => {
    const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return {
      url: window.location.href,
      title: normalize(document.querySelector('h1')?.textContent || document.title),
      text: normalize(document.body?.textContent || '').slice(0, 6000),
      tabs: Array.from(document.querySelectorAll('button, [role="tab"], .native-tab'))
        .map((node) => normalize(node.textContent || ''))
        .filter(Boolean)
        .slice(0, 80),
      console_error_count: 0,
    };
  });
  await page.screenshot({ path: path.join(outDir, `${name}.png`), fullPage: true });
  writeJson(`${name}.json`, data);
  return data;
}

async function openProjectList(page) {
  await page.goto(`${FRONTEND_URL}/a/${ACTION_ID}?menu_id=${MENU_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForPageReady(page);
  await page.waitForFunction((expectedProjectCodeLabel) => {
    const text = String(document.body?.textContent || '');
    return text.includes(expectedProjectCodeLabel) && !text.includes('正在加载列表');
  }, '历史项目编号', { timeout: 90000 });
}

async function openProjectRecord(page) {
  await page.goto(`${FRONTEND_URL}/r/project.project/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForPageReady(page);
}

async function openLegacyTab(page) {
  const legacyTab = page.getByText('历史项目资料', { exact: true }).first();
  await legacyTab.waitFor({ timeout: 20000 });
  await legacyTab.click();
  await page.waitForFunction(() => String(document.body?.textContent || '').includes('历史项目编号'), null, {
    timeout: 20000,
  });
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
    record_id: RECORD_ID,
    artifacts: outDir,
    expected: {
      project_code: EXPECTED_PROJECT_CODE,
      legacy_project_id: EXPECTED_LEGACY_PROJECT_ID,
      company: EXPECTED_COMPANY,
      created_at: EXPECTED_CREATED_AT,
    },
    errors: [],
  };
  const context = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
  const page = await context.newPage();
  attachConsoleCapture(page);
  try {
    await login(page);
    await openProjectList(page);
    const list = await snapshot(page, 'project_list');
    requireIncludes(list.text, '项目台账', 'list_title', result.errors);
    requireIncludes(list.text, '历史项目编号', 'list_legacy_project_code_header', result.errors);

    await openProjectRecord(page);
    const formBefore = await snapshot(page, 'project_form_before_legacy_tab');
    requireIncludes(formBefore.text, '历史项目资料', 'form_legacy_tab_label', result.errors);

    await openLegacyTab(page);
    const legacy = await snapshot(page, 'project_form_legacy_tab');
    requireIncludes(legacy.text, '历史项目编号', 'legacy_tab_project_code_label', result.errors);
    requireIncludes(legacy.text, EXPECTED_PROJECT_CODE, 'legacy_tab_project_code_value', result.errors);
    requireIncludes(legacy.text, EXPECTED_LEGACY_PROJECT_ID, 'legacy_tab_project_id_value', result.errors);
    requireIncludes(legacy.text, EXPECTED_COMPANY, 'legacy_tab_company_value', result.errors);
    requireIncludes(legacy.text, EXPECTED_CREATED_AT, 'legacy_tab_created_at_value', result.errors);

    result.console_errors = page.__consoleErrors || [];
    result.pass = result.errors.length === 0 && result.console_errors.length === 0;
    writeJson('summary.json', result);
    console.log(`[project_legacy_fact_browser_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({ pass: result.pass, errors: result.errors, console_errors: result.console_errors }, null, 2));
    if (!result.pass) process.exit(1);
  } finally {
    await context.close();
    await browser.close();
  }
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[project_legacy_fact_browser_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
