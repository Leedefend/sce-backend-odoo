#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const requireBase = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? path.join(process.cwd(), 'frontend/apps/web/package.json')
  : path.join(process.cwd(), 'package.json');
const { chromium } = createRequire(requireBase)('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5174';
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ACTION_ID = Number(process.env.ACTION_ID || 506);
const MENU_ID = Number(process.env.MENU_ID || 379);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'list-group-clear-acceptance', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  const dbInput = inputs.nth(2);
  if (await dbInput.count().catch(() => 0)) {
    const disabled = await dbInput.isDisabled().catch(() => false);
    if (!disabled) await dbInput.fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 30000 });
}

async function waitReady(page) {
  await page.locator('.template-layout-shell, .page').first().waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    return !text.includes('正在加载列表') && !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function openList(page) {
  await page.goto(`${FRONTEND_URL}/a/${ACTION_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitReady(page);
}

async function openSearchMenu(page) {
  const button = page.locator('.search-menu-toggle').first();
  await button.waitFor({ state: 'visible', timeout: 15000 });
  await button.click();
  await page.locator('.search-dropdown').waitFor({ state: 'visible', timeout: 15000 });
}

async function applyMenuGroup(page) {
  await openSearchMenu(page);
  const groupSection = page.locator('.search-dropdown-section').filter({ hasText: /分组/ }).first();
  const button = groupSection.locator('button.search-menu-item').filter({ hasText: /按项目经理|项目经理/ }).first();
  await button.click();
  await page.waitForFunction(() => new URL(window.location.href).searchParams.has('group_by'), null, { timeout: 15000 });
  await waitReady(page);
  await page.waitForFunction(() => document.querySelectorAll('.grouped-table .group-block').length > 0, null, { timeout: 30000 });
}

async function applyCustomGroup(page) {
  await openSearchMenu(page);
  const groupSection = page.locator('.search-dropdown-section').filter({ hasText: /分组/ }).first();
  const select = groupSection.locator('select.custom-group-select').first();
  await select.waitFor({ state: 'visible', timeout: 15000 });
  const optionValue = await select.locator('option').evaluateAll((options) => {
    const found = options.find((node) => node.getAttribute('value') === 'manager_id')
      || options.find((node) => node.getAttribute('value'));
    return found?.getAttribute('value') || '';
  });
  if (!optionValue) throw new Error('No custom group option found');
  await select.selectOption(optionValue);
  await page.waitForFunction(() => new URL(window.location.href).searchParams.has('group_by'), null, { timeout: 15000 });
  await waitReady(page);
  await page.waitForFunction(() => document.querySelectorAll('.grouped-table .group-block').length > 0, null, { timeout: 30000 });
}

async function clearGroupFacet(page) {
  await page.waitForFunction(() => {
    return Array.from(document.querySelectorAll('.search-facet')).some((node) => {
      if (!(node instanceof HTMLElement)) return false;
      const rect = node.getBoundingClientRect();
      const enabled = !(node instanceof HTMLButtonElement) || !node.disabled;
      return rect.width > 0 && rect.height > 0 && enabled && String(node.textContent || '').includes('项目经理');
    });
  }, null, { timeout: 30000 });
  await page.locator('.search-facet').filter({ hasText: /项目经理/ }).first().click({ force: true });
  await page.waitForFunction(() => !new URL(window.location.href).searchParams.has('group_by'), null, { timeout: 15000 });
  await waitReady(page);
}

async function snapshot(page) {
  return page.evaluate(() => ({
    url: window.location.href,
    facets: Array.from(document.querySelectorAll('.search-facet')).map((node) => String(node.textContent || '').replace(/\s+/g, ' ').trim()),
    grouped_table_count: document.querySelectorAll('.grouped-table').length,
    group_block_count: document.querySelectorAll('.grouped-table .group-block').length,
    flat_table_count: document.querySelectorAll('section.table > table').length,
    flat_row_count: document.querySelectorAll('section.table > table > tbody > tr').length,
    visible_error: String(document.querySelector('.status-panel.error, .validation-error')?.textContent || '').trim(),
  }));
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    artifact_dir: outDir,
    checks: [],
  };
  try {
    await login(page);

    await openList(page);
    await applyMenuGroup(page);
    const menuGrouped = await snapshot(page);
    await clearGroupFacet(page);
    const menuCleared = await snapshot(page);
    summary.checks.push({
      path_id: 'LGC-P01',
      name: 'menu group facet clears grouped route and restores flat list',
      status: menuGrouped.grouped_table_count === 1
        && menuGrouped.group_block_count > 0
        && !new URL(menuCleared.url).searchParams.has('group_by')
        && menuCleared.facets.length === 0
        && menuCleared.flat_table_count === 1
        && menuCleared.flat_row_count > 0
        && !menuCleared.visible_error
        ? 'pass'
        : 'fail',
      grouped: menuGrouped,
      cleared: menuCleared,
    });

    await openList(page);
    await applyCustomGroup(page);
    const customGrouped = await snapshot(page);
    await clearGroupFacet(page);
    const customCleared = await snapshot(page);
    summary.checks.push({
      path_id: 'LGC-P02',
      name: 'custom group facet clears grouped route and restores flat list',
      status: customGrouped.grouped_table_count === 1
        && customGrouped.group_block_count > 0
        && !new URL(customCleared.url).searchParams.has('group_by')
        && customCleared.facets.length === 0
        && customCleared.flat_table_count === 1
        && customCleared.flat_row_count > 0
        && !customCleared.visible_error
        ? 'pass'
        : 'fail',
      grouped: customGrouped,
      cleared: customCleared,
    });
  } catch (err) {
    summary.error = err instanceof Error ? err.stack || err.message : String(err);
  } finally {
    summary.pass = !summary.error && summary.checks.every((row) => row.status === 'pass');
    await page.screenshot({ path: path.join(outDir, summary.pass ? 'final.png' : 'failure.png'), fullPage: true }).catch(() => {});
    writeJson('summary.json', summary);
    await browser.close().catch(() => {});
  }
  console.log(JSON.stringify(summary, null, 2));
  if (!summary.pass) process.exit(1);
}

main().catch((err) => {
  const summary = {
    pass: false,
    error: err instanceof Error ? err.stack || err.message : String(err),
    artifact_dir: outDir,
  };
  writeJson('summary.json', summary);
  console.error(JSON.stringify(summary, null, 2));
  process.exit(1);
});
