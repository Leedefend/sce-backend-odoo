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
const ODOO_URL = process.env.ODOO_URL || 'http://127.0.0.1:8070';
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ACTION_ID = Number(process.env.ACTION_ID || 506);
const MENU_ID = Number(process.env.MENU_ID || 353);
const MODEL = process.env.MVP_MODEL || 'project.project';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'list-native-custom-gap', ts);
const FORBIDDEN_CUSTOM_TEXT = [
  'header_bar',
  'scene-block',
  '{"default_sort"',
  "'kind': 'open'",
  "'visible_profiles'",
  '"filters":[{"key"',
  'project.project.tree',
];

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function attachConsoleCapture(page) {
  page.__consoleErrors = [];
  page.__pageErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') page.__consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    page.__pageErrors.push(err.message);
  });
}

function includesAny(values, target) {
  return values.some((item) => item === target || item.includes(target));
}

function missing(values, expected) {
  return expected.filter((item) => !includesAny(values, item));
}

async function loginCustom(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  const dbInput = inputs.nth(2);
  if ((await dbInput.count().catch(() => 0)) > 0) {
    const disabled = await dbInput.isDisabled().catch(() => false);
    if (!disabled) await dbInput.fill(DB_NAME);
  }
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

async function openCustomList(page) {
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  for (let attempt = 0; attempt < 3; attempt += 1) {
    if (attempt > 0) {
      await page.goto(`${FRONTEND_URL}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.waitForTimeout(800);
    }
    const menuEntry = page.getByRole('button', { name: /项目台账/ }).first();
    if ((await menuEntry.count().catch(() => 0)) > 0) {
      await menuEntry.click();
    } else {
      await page.goto(`${FRONTEND_URL}/s/projects.list?scene_key=projects.list&menu_id=379&action_id=506`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    }
    await page.waitForTimeout(2000);
    await page.waitForFunction(() => {
      const text = String(document.body.textContent || '');
      const app = document.querySelector('#app');
      if (!app || app.children.length === 0 || text.trim().length < 20) return false;
      if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
      const renderedRows = document.querySelectorAll('table tbody > tr').length;
      const degraded = text.includes('高级视图') && text.includes('降级渲染');
      const empty = text.includes('暂无数据') || text.includes('当前页面暂无可显示字段');
      if (renderedRows > 0 || degraded) return true;
      if (empty) return true;
      return false;
    }, null, { timeout: 45000 });
    const rowCount = await page.evaluate(() => document.querySelectorAll('table tbody > tr').length);
    if (rowCount > 0) return;
  }
}

async function openNativeList(page) {
  await page.goto(`${ODOO_URL}/web#model=${MODEL}&view_type=list&action=${ACTION_ID}&menu_id=${MENU_ID}`, { waitUntil: 'domcontentloaded' });
  await page.locator('.o_list_view, .o_content, .o_kanban_view, .o_form_view').first().waitFor({ timeout: 30000 });
}

async function collectCustom(page) {
  return page.evaluate(() => {
    const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const headers = Array.from(document.querySelectorAll('table thead th'))
      .map((node) => normalize(node.textContent))
      .filter(Boolean);
    const blocks = Array.from(document.querySelectorAll('.scene-block'))
      .map((node) => ({
        kind: normalize(node.querySelector('.scene-block__eyebrow')?.textContent || ''),
        title: normalize(node.querySelector('.scene-block__title')?.textContent || ''),
      }));
    const hasViewSwitch = Array.from(document.querySelectorAll('.scene-block__chip'))
      .some((node) => /列表|看板/.test(normalize(node.textContent || '')));
    const bodyText = normalize(document.body?.textContent || '');
    return {
      url: window.location.href,
      readyState: document.readyState,
      title: document.title,
      bodyChildren: document.body ? document.body.children.length : -1,
      appExists: Boolean(document.querySelector('#app')),
      appChildren: document.querySelector('#app') ? document.querySelector('#app').children.length : -1,
      htmlLen: document.documentElement.outerHTML.length,
      bodyTextLen: bodyText.length,
      headers,
      blocks,
      hasSceneBlocks: blocks.length > 0,
      hasToolbarBlock: blocks.some((row) => row.kind === 'toolbar'),
      hasListBlock: blocks.some((row) => row.kind === 'list_view'),
      hasPaginationBlock: blocks.some((row) => row.kind === 'pagination'),
      hasViewSwitch,
      bodySample: bodyText.slice(0, 1200),
      hasRenderError: bodyText.includes('页面渲染失败'),
      hasLoadError: bodyText.includes('页面加载失败'),
      hasEmptyHint: bodyText.includes('暂无数据') || bodyText.includes('当前页面暂无可显示字段'),
      rowCount: document.querySelectorAll('table tbody > tr').length,
    };
  });
}

async function collectNative(page) {
  return page.evaluate(() => {
    const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const headers = Array.from(document.querySelectorAll('.o_list_view thead th, .o_list_table thead th'))
      .map((node) => normalize(node.textContent))
      .filter(Boolean);
    return {
      headers,
      rowCount: document.querySelectorAll('.o_list_view tbody tr, .o_list_table tbody tr').length,
    };
  });
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const report = {
    env: { FRONTEND_URL, ODOO_URL, DB_NAME, ACTION_ID, MENU_ID, MODEL },
    artifacts: outDir,
  };
  try {
    const customPage = await browser.newPage({ viewport: { width: 1440, height: 980 }, locale: 'zh-CN' });
    attachConsoleCapture(customPage);
    await loginCustom(customPage);
    await openCustomList(customPage);
    await customPage.screenshot({ path: path.join(outDir, 'custom_list.png'), fullPage: true });
    report.custom = await collectCustom(customPage);
    report.custom.consoleErrors = customPage.__consoleErrors || [];
    report.custom.pageErrors = customPage.__pageErrors || [];

    const nativePage = await browser.newPage({ viewport: { width: 1440, height: 980 }, locale: 'zh-CN' });
    attachConsoleCapture(nativePage);
    await loginNative(nativePage);
    await openNativeList(nativePage);
    await nativePage.screenshot({ path: path.join(outDir, 'native_list.png'), fullPage: true });
    report.native = await collectNative(nativePage);
    report.native.consoleErrors = nativePage.__consoleErrors || [];
    report.native.pageErrors = nativePage.__pageErrors || [];

    const expectedCustomBlocks = ['toolbar', 'list_view', 'pagination'];
    const customBlockKinds = report.custom.blocks.map((row) => row.kind);
    const blockMissing = missing(customBlockKinds, expectedCustomBlocks);
    const sharedHeaders = report.native.headers.filter((item) => includesAny(report.custom.headers, item));
    const headerCoverage = report.native.headers.length ? sharedHeaders.length / report.native.headers.length : 0;
    const hasRenderedTable = report.custom.rowCount > 0 && report.custom.headers.length > 0;

    report.gap = {
      block_missing: hasRenderedTable ? [] : blockMissing,
      native_headers: report.native.headers.length,
      shared_headers: sharedHeaders.length,
      header_coverage: Number(headerCoverage.toFixed(3)),
      custom_row_count: report.custom.rowCount,
      native_row_count: report.native.rowCount,
      forbidden_text: FORBIDDEN_CUSTOM_TEXT.filter((item) => String(report.custom.bodySample || '').includes(item)),
    };

    report.pass = (hasRenderedTable || blockMissing.length === 0)
      && headerCoverage >= 0.6
      && report.custom.rowCount > 0
      && report.custom.consoleErrors.length === 0
      && report.custom.pageErrors.length === 0
      && report.gap.forbidden_text.length === 0;
    writeJson('summary.json', report);
    console.log(`[list_native_custom_gap_audit] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: report.pass,
      gap: report.gap,
    }, null, 2));
    if (!report.pass) process.exit(1);
  } finally {
    await browser.close().catch(() => undefined);
  }
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[list_native_custom_gap_audit] FAIL: ${err.message}`);
  process.exit(1);
});
