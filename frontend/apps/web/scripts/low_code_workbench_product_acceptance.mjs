#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { chromium } from 'playwright';

const require = createRequire(import.meta.url);
const axeModule = require(require.resolve('@axe-core/playwright', { paths: [path.resolve('node_modules')] }));
const AxeBuilder = axeModule.default || axeModule;
const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:18081';
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const OUT = path.resolve(process.cwd(), '../../../artifacts/playwright/low-code-workbench-product');
const WORKBENCH = `/admin/business-config?db=${encodeURIComponent(DB_NAME)}&root_menu_xmlid=smart_construction_core.menu_sc_root&open_pages=1&model=construction.contract&action_id=1002&page_label=${encodeURIComponent('合同办理')}`;
const PLATFORM_WORKBENCH = `/admin/business-config?db=${encodeURIComponent(DB_NAME)}&root_menu_xmlid=smart_construction_core.menu_sc_root&open_pages=1`;
const ROLES = [
  { key: 'business_config_admin', login: 'wutao', password: '123456', allowed: true },
  { key: 'platform_admin', login: 'sc_fx_scene_admin', password: 'prod_like', allowed: true },
  { key: 'ordinary_user', login: 'demo_role_project_a_member', password: 'demo', allowed: false },
];
const VIEWPORTS = [
  { key: 'desktop', width: 1440, height: 900 },
  { key: 'wide', width: 1920, height: 1080 },
  { key: 'ultrawide', width: 2560, height: 1440 },
  { key: 'tablet', width: 768, height: 1024 },
  { key: 'mobile', width: 390, height: 844 },
];
const TECHNICAL_TERMS = [/\bmodel\b/i, /action\s*id/i, /view\s*id/i, /role\s*key/i, /\bintent\b/i, /\bpayload\b/i, /\bboundary\b/i, /runtime evidence/i, /contract hash/i, /snapshot json/i];

async function login(page, role) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(role.login);
  await inputs.nth(1).fill(role.password);
  if (await inputs.nth(2).isEnabled()) await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 60000 });
  await page.locator('.layout-shell').waitFor({ timeout: 60000 });
}

async function axeBlocking(page) {
  const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  return result.violations.filter((item) => ['critical', 'serious'].includes(item.impact)).map((item) => ({
    id: item.id, impact: item.impact, nodes: item.nodes.length, targets: item.nodes.slice(0, 10).map((node) => node.target),
  }));
}

async function inspectWorkbench(page, viewport) {
  await page.goto(`${BASE_URL}${WORKBENCH}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('[data-lowcode-workbench-ia="three-column"]', { timeout: 60000 });
  await page.waitForFunction(() => document.querySelectorAll('.scan-row').length > 1, null, { timeout: 60000 });
  const bodyText = await page.locator('.business-config-page').innerText();
  const layout = await page.evaluate(() => {
    const rect = (selector) => {
      const element = document.querySelector(selector);
      const box = element?.getBoundingClientRect();
      return box ? { left: box.left, right: box.right, top: box.top, width: box.width } : null;
    };
    const children = ['.page-picker-panel', '.page-config-panel', '.workbench-status-rail'].map(rect);
    return {
      h1Count: document.querySelectorAll('main h1, [role="main"] h1').length,
      documentOverflow: Math.max(0, document.documentElement.scrollWidth - window.innerWidth),
      workspace: rect('[data-lowcode-workbench-ia="three-column"]'),
      regions: children,
      regionCount: children.filter(Boolean).length,
      configStatusOptionCount: document.querySelectorAll('.config-status-filter option').length,
      currentPage: document.querySelector('.selected-page-overview strong')?.textContent?.trim() || '',
    };
  });
  const technicalTerms = TECHNICAL_TERMS.filter((pattern) => pattern.test(bodyText)).map(String);
  const accessibility = await axeBlocking(page);
  const screenshot = path.join(OUT, `workbench-${viewport.key}-${viewport.width}x${viewport.height}.png`);
  await page.screenshot({ path: screenshot, fullPage: true });
  return { viewport, ...layout, technicalTerms, accessibility, screenshot };
}

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true });
const report = { schema_version: 'low_code_workbench_product_acceptance.v1', ok: false, roles: [], viewports: [], keyboard: null, runtime: { console: [], pageerror: [], requestfailed: [] } };
try {
  for (const role of ROLES) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    page.on('console', (message) => { if (message.type() === 'error' && !(role.allowed === false && message.text().includes('403'))) report.runtime.console.push({ role: role.key, text: message.text() }); });
    page.on('pageerror', (error) => report.runtime.pageerror.push({ role: role.key, text: error.message }));
    page.on('requestfailed', (request) => { if (request.failure()?.errorText !== 'net::ERR_ABORTED') report.runtime.requestfailed.push({ role: role.key, url: request.url(), failure: request.failure()?.errorText || '' }); });
    await login(page, role);
    await page.goto(`${BASE_URL}${role.key === 'platform_admin' ? PLATFORM_WORKBENCH : WORKBENCH}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    if (role.allowed) {
      await page.waitForSelector('[data-lowcode-workbench-ia="three-column"]', { timeout: 60000 });
      const text = await page.locator('.business-config-page').innerText();
      report.roles.push({ role: role.key, allowed: true, finalUrl: page.url(), directoryVisible: await page.locator('.page-picker-panel').count(), technicalTerms: TECHNICAL_TERMS.filter((pattern) => pattern.test(text)).map(String), axe: await axeBlocking(page) });
    } else {
      await page.waitForURL((url) => url.pathname.includes('access-denied') || url.pathname.includes('403'), { timeout: 60000 });
      const text = await page.locator('body').innerText();
      const leaked = ['业务页面目录', '配置快照', '当前生效版本', 'ui.business.config.contract', '1215'].filter((term) => text.includes(term));
      report.roles.push({ role: role.key, allowed: false, finalUrl: page.url(), leaked, directoryVisible: await page.locator('.page-picker-panel').count(), axe: await axeBlocking(page) });
    }
    await page.screenshot({ path: path.join(OUT, `role-${role.key}.png`), fullPage: true });
    await context.close();
  }

  const context = await browser.newContext();
  const page = await context.newPage();
  page.on('console', (message) => { if (message.type() === 'error') report.runtime.console.push({ role: 'viewport_matrix', text: message.text() }); });
  page.on('pageerror', (error) => report.runtime.pageerror.push({ role: 'viewport_matrix', text: error.message }));
  page.on('requestfailed', (request) => { if (request.failure()?.errorText !== 'net::ERR_ABORTED') report.runtime.requestfailed.push({ role: 'viewport_matrix', url: request.url(), failure: request.failure()?.errorText || '' }); });
  await login(page, ROLES[0]);
  for (const viewport of VIEWPORTS) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    report.viewports.push(await inspectWorkbench(page, viewport));
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${BASE_URL}${WORKBENCH}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('.scan-row', { timeout: 60000 });
  const rows = page.locator('.scan-row');
  const rowStates = await rows.evaluateAll((nodes) => nodes.map((node) => ({
    name: node.querySelector('.scan-row-main strong')?.textContent?.trim() || '',
    current: node.getAttribute('aria-current') === 'page',
  })));
  const currentIndex = Math.max(0, rowStates.findIndex((row) => row.current));
  const direction = currentIndex < rowStates.length - 1 ? 'ArrowDown' : 'ArrowUp';
  const targetIndex = direction === 'ArrowDown' ? currentIndex + 1 : currentIndex - 1;
  await rows.nth(currentIndex).focus();
  const before = await page.locator('.selected-page-overview strong').innerText();
  await page.keyboard.press(direction);
  await page.waitForFunction((target) => document.querySelector('.selected-page-overview strong')?.textContent?.trim() === target, rowStates[targetIndex].name, { timeout: 60000 });
  report.keyboard = {
    before,
    direction,
    after: await page.locator('.selected-page-overview strong').innerText(),
    focusedRow: await page.locator('.scan-row:focus .scan-row-main strong').innerText(),
  };
  await context.close();

  const allowedRolesPass = report.roles.filter((row) => row.allowed).length === 2
    && report.roles.filter((row) => row.allowed).every((row) => row.directoryVisible === 1 && row.technicalTerms.length === 0 && row.axe.length === 0);
  const denied = report.roles.find((row) => !row.allowed);
  const deniedPass = denied && denied.directoryVisible === 0 && denied.leaked.length === 0 && denied.axe.length === 0;
  const viewportPass = report.viewports.length === 5 && report.viewports.every((row) => row.h1Count === 1 && row.documentOverflow === 0 && row.regionCount === 3 && row.configStatusOptionCount === 4 && row.technicalTerms.length === 0 && row.accessibility.length === 0);
  report.assertions = {
    two_admin_authorities: allowedRolesPass,
    ordinary_user_safe_403: Boolean(deniedPass),
    five_viewports: viewportPass,
    keyboard_up_down_selection: Boolean(report.keyboard?.after && report.keyboard.after === report.keyboard.focusedRow && report.keyboard.after !== report.keyboard.before),
    no_console_pageerror_requestfailed: report.runtime.console.length === 0 && report.runtime.pageerror.length === 0 && report.runtime.requestfailed.length === 0,
  };
  report.ok = Object.values(report.assertions).every(Boolean);
} catch (error) {
  report.failure = error instanceof Error ? error.message : String(error);
} finally {
  await browser.close();
  await fs.writeFile(path.join(OUT, 'report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8');
}

if (!report.ok) {
  console.error('[low_code_workbench_product_acceptance] FAIL', report.failure || report.assertions);
  process.exit(1);
}
console.log('[low_code_workbench_product_acceptance] PASS roles=3 viewports=5 axe=0 overflow=0');
