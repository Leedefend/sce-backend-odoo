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
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5174';
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'demo_role_pm';
const PASSWORD = process.env.E2E_PASSWORD || 'demo';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.join(ROOT_DIR, 'artifacts');
const REPORT_JSON = path.join(ARTIFACTS_DIR, 'backend', 'user_page_delivery_surface_browser_acceptance.json');

function ensureDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}&t=${Date.now()}`, { waitUntil: 'networkidle' });
  await page.locator('input[autocomplete="username"]').fill(LOGIN);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  const dbInput = page.locator('input[autocomplete="off"]');
  if (await dbInput.isEditable().catch(() => false)) {
    await dbInput.fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 30000 });
  await page.waitForLoadState('networkidle').catch(() => {});
}

async function main() {
  const browser = await chromium.launch({ headless: String(process.env.HEADLESS || '1') !== '0' });
  const context = await browser.newContext({ viewport: { width: 1440, height: 960 } });
  const page = await context.newPage();
  const errors = [];
  try {
    await login(page);
    await page.goto(`${FRONTEND_URL}/delivery?t=${Date.now()}`, { waitUntil: 'networkidle' });
    await page.getByText('用户页面交付看板').waitFor({ timeout: 15000 });
    const body = normalize(await page.locator('body').innerText());
    for (const text of ['标准交付包 V1', '10 个交付模块', '关键旅程', '角色包', '验收证据', '项目立项与台账', '付款申请与审批', '老板/领导']) {
      if (!body.includes(text)) errors.push(`missing_text:${text}`);
    }
    const moduleRows = await page.locator('.module-row').count();
    if (moduleRows < 11) errors.push(`module_rows=${moduleRows}`);
    const roleCards = await page.locator('.role-card').count();
    if (roleCards < 6) errors.push(`role_cards=${roleCards}`);
    await page.getByRole('button', { name: /projects\.list/ }).first().click();
    await page.waitForURL((url) => url.pathname === '/s/projects.list', { timeout: 10000 });
  } catch (err) {
    errors.push(err && err.message ? err.message : String(err));
  } finally {
    await context.close();
    await browser.close();
  }

  const report = {
    ok: errors.length === 0,
    frontend_url: FRONTEND_URL,
    db_name: DB_NAME,
    login: LOGIN,
    errors,
  };
  ensureDir(REPORT_JSON);
  fs.writeFileSync(REPORT_JSON, JSON.stringify(report, null, 2) + '\n', 'utf8');
  if (!report.ok) {
    console.error(`[user_page_delivery_surface_browser_acceptance] FAIL ${REPORT_JSON}`);
    console.error(JSON.stringify(report, null, 2));
    process.exit(1);
  }
  console.log(`[user_page_delivery_surface_browser_acceptance] PASS ${REPORT_JSON}`);
}

main().catch((err) => {
  console.error(`[user_page_delivery_surface_browser_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
