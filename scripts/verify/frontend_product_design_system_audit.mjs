#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { launchChromium } from './playwright_runtime.mjs';

const require = createRequire(import.meta.url);
const axeModule = require(require.resolve('@axe-core/playwright', { paths: [path.resolve('frontend/apps/web/node_modules')] }));
const AxeBuilder = axeModule.default || axeModule;

const BASE_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const DB_NAME = process.env.DB_NAME || 'sc_frontend_acceptance';
const PASSWORD = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const PHASE = process.env.FE_PRO_04_PHASE === 'final' ? 'final' : 'baseline';
const ROOT = process.env.FE_PRO_04_ARTIFACT_ROOT || 'artifacts/frontend-professional/fe-pro-04';
const OUTPUT = path.join(ROOT, PHASE);
const REPORT = path.join(ROOT, `${PHASE}-report.json`);
const TARGETS = JSON.parse(process.env.FRONTEND_DELIVERY_HARDENING_TARGETS_JSON || '{}');
const VIEWPORTS = [
  { width: 1440, height: 900 },
  { width: 1280, height: 800 },
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
];
const DARK_CASES = new Set(['finance_home', 'my_work', 'contract_list', 'contract_detail', 'payment_request_create', 'approval_dialog', 'network_error']);
const TECHNICAL_TERMS = ['payload', 'bundle', 'fallback', 'HUD', 'trace', 'JSON', 'registry', 'projection', 'provider', 'debug', 'capability map', '配置缺口', '契约未命中'];

fs.mkdirSync(OUTPUT, { recursive: true });

function check(value, message) { if (!value) throw new Error(message); }
function recordRoute(target) { return `/r/${target.model}/${target.record_id}?action_id=${target.action_id}&menu_id=${target.menu_id}`; }
function formRoute(target, id = target.record_id) { return `/f/${target.model}/${id}?action_id=${target.action_id}&menu_id=${target.menu_id}`; }
function listRoute(target) { return `/a/${target.action_id}?menu_id=${target.menu_id}`; }

const ALL_CASES = [
  { key: 'finance_home', role: 'demo_role_finance', route: '/' },
  { key: 'project_member_home', role: 'demo_role_project_a_member', route: '/' },
  { key: 'my_work', role: 'demo_role_finance', route: '/my-work' },
  { key: 'project_list', role: 'demo_role_pm', route: () => listRoute(TARGETS.project) },
  { key: 'contract_list', role: 'demo_role_pm', route: () => listRoute(TARGETS.contract) },
  { key: 'payment_request_list', role: 'demo_role_finance', route: () => listRoute(TARGETS.payment_request) },
  { key: 'contract_detail', role: 'demo_role_pm', route: () => recordRoute(TARGETS.contract) },
  { key: 'settlement_detail', role: 'demo_role_finance', route: () => recordRoute(TARGETS.settlement) },
  { key: 'payment_request_detail', role: 'demo_role_finance', route: () => recordRoute(TARGETS.payment_request) },
  { key: 'payment_execution_detail', role: 'demo_role_finance', route: () => recordRoute(TARGETS.payment_execution) },
  { key: 'contract_form', role: 'demo_role_pm', route: () => formRoute(TARGETS.contract) },
  { key: 'payment_request_create', role: 'demo_role_finance', mode: 'create', route: () => recordRoute(TARGETS.work_settlement) },
  { key: 'payment_request_edit', role: 'demo_role_finance', route: () => formRoute(TARGETS.payment_request) },
  { key: 'permission_denied', role: 'demo_role_project_a_member', mode: 'denied', route: () => recordRoute(TARGETS.payment_request) },
  { key: 'not_found', role: 'demo_role_finance', mode: 'not-found', route: () => `/r/${TARGETS.payment_request.model}/999999?action_id=${TARGETS.payment_request.action_id}&menu_id=${TARGETS.payment_request.menu_id}` },
  { key: 'conflict', role: 'demo_role_finance', mode: 'conflict', route: () => recordRoute(TARGETS.payment_request) },
  { key: 'empty_list', role: 'demo_role_finance', mode: 'empty', route: () => listRoute(TARGETS.payment_request) },
  { key: 'network_error', role: 'demo_role_finance', mode: 'network', route: () => recordRoute(TARGETS.payment_request) },
];
const CASE_FILTER = String(process.env.FE_PRO_04_CASE || '').trim();
const CASES = CASE_FILTER ? ALL_CASES.filter((entry) => entry.key === CASE_FILTER) : ALL_CASES;
check(CASES.length > 0, `unknown FE_PRO_04_CASE=${CASE_FILTER}`);
const DARK_ONLY_CASES = [
  { key: 'approval_dialog', role: 'demo_role_finance', mode: 'dialog', route: () => recordRoute(TARGETS.journey_request) },
];

function runtimeCapture(page) {
  const state = { console: [], pageerror: [], http: [], expected_http: [] };
  page.on('console', (message) => {
    if (message.type() === 'error' && !/favicon|ResizeObserver|Failed to load resource/i.test(message.text())) state.console.push(message.text());
  });
  page.on('pageerror', (error) => state.pageerror.push(error.message));
  page.on('response', (response) => {
    if (response.status() < 400 || !response.url().includes('/api/v1/')) return;
    const row = { status: response.status(), url: response.url() };
    if ([403, 404, 409, 500].includes(response.status())) state.expected_http.push(row);
    else state.http.push(row);
  });
  return state;
}

async function login(page, user) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('#login-username, input[autocomplete="username"]').first().fill(user);
  await page.locator('#login-password, input[autocomplete="current-password"]').first().fill(PASSWORD);
  const db = page.locator('input').nth(2);
  if (await db.isEnabled().catch(() => false)) await db.fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
}

function fulfillError(route, status, code, message) {
  return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify({ error: { message, reason_code: code, retryable: true } }) });
}

async function interceptTargetRead(page, target, handler) {
  let used = false;
  const callback = async (route) => {
    let payload = {};
    try { payload = JSON.parse(route.request().postData() || '{}'); } catch {}
    const params = payload.params || {};
    const ids = Array.isArray(params.ids) ? params.ids.map(Number) : [];
    const matches = payload.intent === 'api.data'
      && params.op === 'read'
      && params.model === target.model
      && ids.includes(Number(target.record_id));
    if (matches && !used) {
      used = true;
      await handler(route);
      return;
    }
    await route.continue();
  };
  await page.route('**/api/v1/intent**', callback);
  return async () => page.unroute('**/api/v1/intent**', callback);
}

async function prepareCase(page, entry) {
  let removeFault = null;
  if (entry.mode === 'network') removeFault = await interceptTargetRead(page, TARGETS.payment_request, (route) => route.abort('failed'));
  if (entry.mode === 'conflict') removeFault = await interceptTargetRead(page, TARGETS.payment_request, (route) => fulfillError(route, 409, 'CONFLICT', 'stale record'));
  const route = typeof entry.route === 'function' ? entry.route() : entry.route;
  await page.goto(`${BASE_URL}${route}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  if (entry.key.endsWith('_list') && entry.mode !== 'empty') {
    await page.locator([
      'main .action-toolbar input[type="search"]:visible',
      'main .product-list-header__search input[type="search"]:visible',
    ].join(', ')).first().waitFor({ state: 'visible', timeout: 45000 });
  }
  if (entry.mode === 'create') {
    await page.locator('.financial-workspace[data-workspace-kind="settlement"]').waitFor({ timeout: 45000 });
    await page.getByRole('button', { name: '新建付款申请', exact: true }).click();
    await page.waitForURL((url) => url.pathname.includes('/f/payment.request/new'), { timeout: 45000 });
  } else if (entry.mode === 'empty') {
    await page.locator('main [data-product-page-mode="list"]').first().waitFor({ timeout: 45000 });
    const search = page.locator('main input[type="search"]:visible, main input[placeholder*="搜索"]:visible').first();
    await search.waitFor({ state: 'visible', timeout: 45000 });
    await search.fill('__FE_PRO_04_NO_MATCH__');
    await search.press('Enter');
    await page.locator('main .sc-empty, main .list-empty-state').first().waitFor({ state: 'visible', timeout: 45000 });
  } else if (entry.mode === 'dialog') {
    await page.locator('.financial-workspace[data-workspace-kind="payment_request"]').waitFor({ timeout: 45000 });
    await page.locator('.template-page-header-actions button.sc-btn-primary').filter({ hasText: /^提交$/ }).first().click();
    await page.getByRole('dialog').waitFor({ timeout: 15000 });
  }
  const expectedHeading = {
    denied: '无权访问',
    'not-found': '记录不存在',
    conflict: '数据已发生变化',
    network: '网络连接异常',
  }[entry.mode];
  if (expectedHeading) await page.getByRole('heading', { name: expectedHeading }).first().waitFor({ timeout: 45000 });
  else await page.locator('main').waitFor({ timeout: 45000 });
  await page.waitForFunction(
    () => !/(正在初始化|正在加载|加载中)/.test(document.body.textContent || ''),
    { timeout: 45000 },
  );
  await page.waitForTimeout(300);
  if (removeFault) await removeFault();
}

async function visualMetrics(page, runDetailedScan) {
  if (!runDetailedScan) {
    const compact = await page.evaluate(() => ({
      title: document.querySelector('h1')?.textContent?.trim() || '',
      h1_count: document.querySelectorAll('h1').length,
      main_count: document.querySelectorAll('main').length,
      horizontal_overflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
    }));
    return {
      ...compact,
      technical_term_hits: [],
      axe_critical_serious: [],
    };
  }
  const metrics = await page.evaluate(() => {
    const visible = (node) => {
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    };
    const main = document.querySelector('main');
    const nodes = main ? [...main.querySelectorAll('*')].filter(visible) : [];
    const fontSizes = [...new Set(nodes.map((node) => window.getComputedStyle(node).fontSize))];
    const fontLevels = [...new Set(fontSizes.map((value) => {
      const size = Number.parseFloat(value);
      if (size <= 12.5) return 'supporting';
      if (size <= 15) return 'body';
      if (size <= 20) return 'section';
      return 'page';
    }))];
    const buttons = [...document.querySelectorAll('button, [role="button"]')].filter(visible);
    const buttonStyles = [...new Set(buttons.map((node) => {
      const style = window.getComputedStyle(node);
      return [style.height, style.backgroundColor, style.borderColor, style.borderRadius, style.fontWeight].join('|');
    }))];
    const badges = [...document.querySelectorAll('[class*="status"], .sc-tag, .sc-badge')].filter(visible);
    const badgeStyles = [...new Set(badges.map((node) => {
      const style = window.getComputedStyle(node);
      return [style.color, style.backgroundColor, style.borderColor, style.borderRadius].join('|');
    }))];
    const inputs = [...document.querySelectorAll('input, select, textarea')].filter(visible);
    const inputHeights = [...new Set(inputs.map((node) => Math.round(node.getBoundingClientRect().height)))];
    const borders = nodes.filter((node) => {
      const style = window.getComputedStyle(node);
      return ['Top', 'Right', 'Bottom', 'Left'].some((side) => parseFloat(style[`border${side}Width`]) > 0 && style[`border${side}Style`] !== 'none');
    }).length;
    const panels = [...document.querySelectorAll('main .sc-panel, main [class*="panel"], main [class*="card"]')].filter(visible).length;
    const rect = main?.getBoundingClientRect();
    return {
      title: document.querySelector('h1')?.textContent?.trim() || '',
      h1_count: [...document.querySelectorAll('h1')].filter(visible).length,
      main_count: [...document.querySelectorAll('main')].filter(visible).length,
      font_size_count: fontSizes.length,
      font_sizes: fontSizes,
      font_level_count: fontLevels.length,
      font_levels: fontLevels,
      panel_card_count: panels,
      button_style_count: buttonStyles.length,
      status_style_count: badgeStyles.length,
      input_heights: inputHeights,
      page_left_margin: rect ? Math.round(rect.left) : null,
      page_right_margin: rect ? Math.round(window.innerWidth - rect.right) : null,
      content_max_width: main ? window.getComputedStyle(main).maxWidth : '',
      border_count: borders,
      first_screen_actions: buttons.filter((node) => {
        const box = node.getBoundingClientRect();
        return box.top >= 0 && box.top < window.innerHeight;
      }).length,
      visible_element_count: nodes.length,
      horizontal_overflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
    };
  });
  const text = await page.evaluate(() => document.body.textContent || '');
  const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  return {
    ...metrics,
    technical_term_hits: TECHNICAL_TERMS.filter((term) => text.toLowerCase().includes(term.toLowerCase())),
    axe_critical_serious: axe.violations.filter((row) => ['critical', 'serious'].includes(row.impact)).map((row) => ({ id: row.id, impact: row.impact, nodes: row.nodes.length })),
  };
}

async function captureEntry(browser, entry, theme = 'light') {
  console.log(`[fe-pro-04] ${entry.key}:${theme}:login`);
  const context = await browser.newContext({ viewport: VIEWPORTS[0], locale: 'zh-CN', colorScheme: theme });
  const page = await context.newPage();
  const runtime = runtimeCapture(page);
  await login(page, entry.role);
  if (theme === 'dark') await page.evaluate(() => document.documentElement.setAttribute('data-sc-theme', 'dark'));
  console.log(`[fe-pro-04] ${entry.key}:${theme}:open`);
  await prepareCase(page, entry);
  if (theme === 'dark') await page.evaluate(() => document.documentElement.setAttribute('data-sc-theme', 'dark'));
  const company = await page.getByLabel('当前公司').inputValue({ timeout: 2000 }).catch(() => '');
  const rows = [];
  const viewports = theme === 'dark' ? [{ width: 1440, height: 900 }] : VIEWPORTS;
  for (const viewport of viewports) {
    console.log(`[fe-pro-04] ${entry.key}:${theme}:${viewport.width}x${viewport.height}`);
    const viewportStarted = Date.now();
    await page.setViewportSize(viewport);
    await page.waitForTimeout(120);
    const screenshot = path.join(OUTPUT, `${entry.key}-${theme}-${viewport.width}x${viewport.height}.png`);
    await page.screenshot({ path: screenshot, fullPage: false, timeout: 5000 });
    console.log(`[fe-pro-04] ${entry.key}:${theme}:${viewport.width}x${viewport.height}:captured_ms=${Date.now() - viewportStarted}`);
    rows.push({
      surface: entry.key,
      role: entry.role,
      company,
      viewport: `${viewport.width}x${viewport.height}`,
      theme,
      route: new URL(page.url()).pathname,
      component_contract_version: 'sc-product-design-system.v1',
      screenshot,
      screenshot_sha256: '',
      accessibility_scanned: viewport.width === 1440,
      ...(await visualMetrics(page, viewport.width === 1440)),
    });
  }
  await context.close();
  return { rows, runtime };
}

function lineCount(file) { return fs.readFileSync(file, 'utf8').split('\n').length - 1; }

async function captureEntryWithRetry(browser, entry, theme) {
  try {
    return await captureEntry(browser, entry, theme);
  } catch (error) {
    process.stderr.write(`[fe-pro-04] ${entry.key}:${theme}:retry ${error instanceof Error ? error.message.split('\n')[0] : 'unknown error'}\n`);
    return captureEntry(browser, entry, theme);
  }
}

async function main() {
  for (const key of ['project', 'contract', 'settlement', 'payment_request', 'payment_execution', 'work_settlement']) check(TARGETS[key]?.record_id > 0, `missing target ${key}`);
  const browser = await launchChromium({ headless: true });
  try {
    const pages = [];
    const runtime = [];
    for (const entry of CASES) {
      const light = await captureEntryWithRetry(browser, entry, 'light');
      pages.push(...light.rows); runtime.push({ surface: entry.key, theme: 'light', ...light.runtime });
      if (PHASE === 'final' && DARK_CASES.has(entry.key)) {
        const dark = await captureEntryWithRetry(browser, entry, 'dark');
        pages.push(...dark.rows); runtime.push({ surface: entry.key, theme: 'dark', ...dark.runtime });
      }
    }
    if (PHASE === 'final') {
      for (const entry of DARK_ONLY_CASES) {
        const dark = await captureEntryWithRetry(browser, entry, 'dark');
        pages.push(...dark.rows); runtime.push({ surface: entry.key, theme: 'dark', ...dark.runtime });
      }
    }
    for (const row of pages) {
      const digest = createHash('sha256').update(fs.readFileSync(row.screenshot)).digest('hex');
      row.screenshot_sha256 = digest;
    }
    const report = {
      schema_version: 'frontend_product_design_system_audit.v1',
      phase: PHASE,
      git_sha: process.env.GIT_SHA || '',
      database: DB_NAME,
      base_url: BASE_URL,
      page_count: CASES.length,
      pages,
      runtime,
      source_size: {
        app_shell: lineCount('frontend/apps/web/src/layouts/AppShell.vue'),
        list_page: lineCount('frontend/apps/web/src/pages/ListPage.vue'),
        action_view: lineCount('frontend/apps/web/src/views/ActionView.vue'),
        contract_form_page: lineCount('frontend/apps/web/src/pages/ContractFormPage.vue'),
        my_work_approval_workspace: lineCount('frontend/apps/web/src/components/business/MyWorkApprovalWorkspace.vue'),
      },
    };
    fs.writeFileSync(REPORT, `${JSON.stringify(report, null, 2)}\n`);
    if (PHASE === 'final') {
      const baselinePath = path.join(ROOT, 'baseline-report.json');
      check(fs.existsSync(baselinePath), `missing baseline report: ${baselinePath}`);
      const baseline = JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
      const comparison = {
        schema_version: 'frontend_product_design_system_visual_regression.v1',
        baseline_sha: baseline.git_sha,
        final_sha: report.git_sha,
        component_contract_version: 'sc-product-design-system.v1',
        surfaces: report.pages.filter((row) => row.theme === 'light').map((row) => {
          const before = baseline.pages.find((item) => item.surface === row.surface && item.theme === row.theme && item.viewport === row.viewport) || null;
          return {
            surface: row.surface,
            viewport: row.viewport,
            theme: row.theme,
            route: row.route,
            baseline_screenshot_sha256: before?.screenshot_sha256 || null,
            final_screenshot_sha256: row.screenshot_sha256,
            structural_metrics: {
              before: before ? { h1_count: before.h1_count, main_count: before.main_count, panel_card_count: before.panel_card_count, first_screen_actions: before.first_screen_actions, horizontal_overflow: before.horizontal_overflow } : null,
              after: { h1_count: row.h1_count, main_count: row.main_count, panel_card_count: row.panel_card_count, first_screen_actions: row.first_screen_actions, horizontal_overflow: row.horizontal_overflow },
            },
          };
        }),
      };
      fs.writeFileSync(path.join(ROOT, 'visual-regression-report.json'), `${JSON.stringify(comparison, null, 2)}\n`);
      check(pages.filter((row) => row.theme === 'light').length === CASES.length * VIEWPORTS.length, 'light visual matrix incomplete');
      check(pages.filter((row) => row.theme === 'dark').length === DARK_CASES.size, 'dark visual sample incomplete');
      check(!pages.some((row) => row.h1_count !== 1 || row.main_count !== 1), 'page landmark hierarchy failed');
      check(!pages.some((row) => row.font_level_count > 4), 'page typography hierarchy exceeds four visible levels');
      check(!pages.some((row) => row.horizontal_overflow > 1 || row.axe_critical_serious.length), 'responsive/accessibility visual guard failed');
      check(!pages.some((row) => row.technical_term_hits.length), 'technical product wording found');
      check(!runtime.some((row) => row.console.length || row.pageerror.length || row.http.length), 'unexpected runtime errors found');
    }
    console.log(JSON.stringify({ report: REPORT, phase: PHASE, surfaces: CASES.length, rows: pages.length }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(`[frontend_product_design_system_audit] ${error.stack || error.message}`);
  process.exitCode = 2;
});
