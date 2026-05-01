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
const ODOO_URL = process.env.ODOO_URL || 'http://127.0.0.1:18069';
const DB_NAME = process.env.DB_NAME || 'sc_prod_sim';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const MODEL = process.env.MVP_MODEL || 'project.project';
const RECORD_ID = process.env.RECORD_ID || '771';
const ACTION_ID = process.env.ACTION_ID || '506';
const MENU_ID = process.env.MENU_ID || '353';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-smart-button-overflow', ts);

const DIRECT_SMART = ['执行结构', '工程量清单', '预算/成本', '合同'];
const OVERFLOW_SMART = ['物资/采购', '结算/财务'];

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

function includesLabel(values, label) {
  return values.some((value) => value === label || value.includes(label));
}

async function loginCustom(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 });
}

async function loginNative(page) {
  await page.goto(`${ODOO_URL}/web/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
  const dbInput = page.locator('input[name="db"]');
  if (await dbInput.count().catch(() => 0)) await dbInput.fill(DB_NAME);
  await page.locator('input[name="login"]').fill(LOGIN);
  await page.locator('input[name="password"]').fill(PASSWORD);
  await page.locator('button[type="submit"], input[type="submit"]').first().click();
  await page.waitForURL((url) => !url.pathname.includes('/web/login'), { timeout: 30000 });
}

async function openCustom(page) {
  await page.goto(`${FRONTEND_URL}/r/${MODEL}/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    return !text.includes('正在加载页面')
      && !text.includes('页面加载失败')
      && document.querySelectorAll('button.native-action-btn--smart').length > 0;
  }, null, { timeout: 30000 });
}

async function openNative(page) {
  await page.goto(`${ODOO_URL}/web#id=${RECORD_ID}&model=${MODEL}&view_type=form&action=${ACTION_ID}&menu_id=${MENU_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await page.locator('.o_form_view').waitFor({ timeout: 30000 });
  await page.getByRole('button', { name: /^更多$/ }).first().waitFor({ timeout: 30000 });
}

async function collectNative(page) {
  const direct = await page.evaluate(() => Array.from(document.querySelectorAll('button.oe_stat_button'))
    .map((node) => String(node.textContent || '').replace(/\s+/g, ' ').trim())
    .filter(Boolean));
  const nativeMore = page.locator('button.o_button_more').first();
  const moreVisible = await nativeMore.isVisible().catch(() => false);
  let overflow = [];
  if (moreVisible) {
    await nativeMore.click();
    await page.locator('.dropdown-menu.show, .o-dropdown--menu').first().waitFor({ timeout: 5000 }).catch(() => {});
    overflow = await page.evaluate(() => Array.from(document.querySelectorAll('.dropdown-menu.show .dropdown-item, .dropdown-menu.show button, .o-dropdown--menu .dropdown-item, .o-dropdown--menu button'))
      .map((node) => String(node.textContent || '').replace(/\s+/g, ' ').trim())
      .filter(Boolean));
  }
  return { direct, more_visible: moreVisible, overflow };
}

async function collectCustom(page) {
  const groups = await page.evaluate(() => Array.from(document.querySelectorAll('.native-actions--smart')).map((group) => ({
    direct: Array.from(group.querySelectorAll(':scope > button.native-action-btn, :scope > .native-action-more > button.native-action-btn'))
      .map((node) => String(node.textContent || '').replace(/\s+/g, ' ').trim())
      .filter(Boolean),
    overflow_before_open: Array.from(group.querySelectorAll('.native-action-more-menu button'))
      .map((node) => String(node.textContent || '').replace(/\s+/g, ' ').trim())
      .filter(Boolean),
  })));
  const targetIndex = groups.findIndex((group) => DIRECT_SMART.every((label) => includesLabel(group.direct, label)));
  if (targetIndex >= 0) {
    await page.locator('.native-actions--smart').nth(targetIndex).locator('.native-action-btn--more').click();
  }
  const afterOpen = await page.evaluate((index) => {
    const group = Array.from(document.querySelectorAll('.native-actions--smart'))[index];
    if (!group) return [];
    return Array.from(group.querySelectorAll('.native-action-more-menu button'))
      .map((node) => String(node.textContent || '').replace(/\s+/g, ' ').trim())
      .filter(Boolean);
  }, targetIndex);
  return {
    groups,
    target_index: targetIndex,
    overflow_after_open: afterOpen,
  };
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
    odoo_url: ODOO_URL,
    artifact_dir: outDir,
  };
  try {
    const nativeContext = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
    const nativePage = await nativeContext.newPage();
    attachConsoleCapture(nativePage);
    await loginNative(nativePage);
    await openNative(nativePage);
    result.native = await collectNative(nativePage);
    await nativePage.screenshot({ path: path.join(outDir, 'native_more_open.png'), fullPage: true });
    result.native_console_errors = nativePage.__consoleErrors || [];
    await nativeContext.close();

    const customContext = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
    const customPage = await customContext.newPage();
    attachConsoleCapture(customPage);
    await loginCustom(customPage);
    await openCustom(customPage);
    result.custom = await collectCustom(customPage);
    await customPage.screenshot({ path: path.join(outDir, 'custom_more_open.png'), fullPage: true });
    result.custom_console_errors = customPage.__consoleErrors || [];
    await customContext.close();

    const nativeDirectOk = DIRECT_SMART.every((label) => includesLabel(result.native.direct, label)) && result.native.more_visible;
    const nativeOverflowOk = OVERFLOW_SMART.every((label) => includesLabel(result.native.overflow, label))
      && result.native.overflow.some((label) => label.includes('投标'));
    const customDirect = result.custom.groups[result.custom.target_index]?.direct || [];
    const customDirectOk = DIRECT_SMART.every((label) => includesLabel(customDirect, label)) && includesLabel(customDirect, '更多');
    const customOverflowOk = OVERFLOW_SMART.every((label) => includesLabel(result.custom.overflow_after_open, label))
      && result.custom.overflow_after_open.some((label) => label.includes('投标'));

    result.checks = [
      { path_id: 'P16', name: 'native smart button box exposes direct buttons and more overflow', status: nativeDirectOk && nativeOverflowOk ? 'pass' : 'fail' },
      { path_id: 'P16', name: 'custom smart button box mirrors direct buttons and more overflow', status: customDirectOk && customOverflowOk ? 'pass' : 'fail' },
    ];
    result.pass = result.checks.every((row) => row.status === 'pass')
      && result.native_console_errors.length === 0
      && result.custom_console_errors.length === 0;
    writeJson('summary.json', result);
    console.log(`[form_smart_button_overflow_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: result.pass,
      checks: result.checks,
      native_overflow: result.native.overflow,
      custom_overflow: result.custom.overflow_after_open,
      console_errors: {
        native: result.native_console_errors.length,
        custom: result.custom_console_errors.length,
      },
    }, null, 2));
    if (!result.pass) process.exit(1);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[form_smart_button_overflow_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
