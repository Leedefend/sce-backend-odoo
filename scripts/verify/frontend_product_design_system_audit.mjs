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
const FORM_CANVAS_AUDIT = Boolean(process.env.FE_PRO_04WR2_PHASE);
const WORKSPACE_COMPAT_AUDIT = Boolean(process.env.FE_PRO_04WR1_PHASE);
const WORKSPACE_AUDIT = FORM_CANVAS_AUDIT || WORKSPACE_COMPAT_AUDIT || Boolean(process.env.FE_PRO_04WR_PHASE);
const WIDTH_AUDIT = Boolean(process.env.FE_PRO_04W_PHASE);
const PHASE_SOURCE = FORM_CANVAS_AUDIT
  ? process.env.FE_PRO_04WR2_PHASE
  : WORKSPACE_COMPAT_AUDIT
  ? process.env.FE_PRO_04WR1_PHASE
  : WORKSPACE_AUDIT
  ? process.env.FE_PRO_04WR_PHASE
  : (WIDTH_AUDIT ? process.env.FE_PRO_04W_PHASE : process.env.FE_PRO_04_PHASE);
const PHASE = PHASE_SOURCE === 'final' ? 'final' : 'baseline';
const ROOT = FORM_CANVAS_AUDIT
  ? (process.env.FE_PRO_04WR2_ARTIFACT_ROOT || 'artifacts/frontend-professional/fe-pro-04wr2')
  : WORKSPACE_COMPAT_AUDIT
  ? (process.env.FE_PRO_04WR1_ARTIFACT_ROOT || 'artifacts/frontend-professional/fe-pro-04wr1')
  : WORKSPACE_AUDIT
  ? (process.env.FE_PRO_04WR_ARTIFACT_ROOT || 'artifacts/frontend-professional/fe-pro-04wr')
  : (WIDTH_AUDIT
      ? (process.env.FE_PRO_04W_ARTIFACT_ROOT || 'artifacts/frontend-professional/fe-pro-04w')
      : (process.env.FE_PRO_04_ARTIFACT_ROOT || 'artifacts/frontend-professional/fe-pro-04'));
const OUTPUT = path.join(ROOT, PHASE);
const REPORT = path.join(ROOT, `${PHASE}-report.json`);
const TARGETS = JSON.parse(process.env.FRONTEND_DELIVERY_HARDENING_TARGETS_JSON || '{}');
const VIEWPORTS = FORM_CANVAS_AUDIT
  ? [
      { width: 1440, height: 900 },
      { width: 1920, height: 1080 },
      { width: 2560, height: 1440 },
      { width: 768, height: 1024 },
      { width: 390, height: 844 },
    ]
  : WORKSPACE_COMPAT_AUDIT
  ? [
      { width: 1920, height: 1080 },
      { width: 390, height: 844 },
    ]
  : WORKSPACE_AUDIT
  ? (PHASE === 'final'
      ? [
          { width: 1440, height: 900 },
          { width: 1920, height: 1080 },
          { width: 2560, height: 1440 },
          { width: 390, height: 844 },
        ]
      : [{ width: 1920, height: 1080 }])
  : WIDTH_AUDIT
  ? [
      { width: 1440, height: 900 },
      { width: 1920, height: 1080 },
      { width: 2560, height: 1440 },
      { width: 390, height: 844 },
    ]
  : [
      { width: 1440, height: 900 },
      { width: 1280, height: 800 },
      { width: 768, height: 1024 },
      { width: 390, height: 844 },
    ];
const DARK_CASES = new Set(FORM_CANVAS_AUDIT
  ? ['payment_request_create', 'contract_form']
  : WORKSPACE_COMPAT_AUDIT
  ? []
  : WORKSPACE_AUDIT
  ? ['contract_list', 'contract_detail', 'contract_form', 'payment_request_create', 'permission_denied']
  : (WIDTH_AUDIT
      ? ['my_work', 'contract_list', 'contract_detail', 'payment_request_create']
      : ['finance_home', 'my_work', 'contract_list', 'contract_detail', 'payment_request_create', 'approval_dialog', 'network_error']));
const TECHNICAL_TERMS = ['payload', 'bundle', 'fallback', 'HUD', 'trace', 'JSON', 'registry', 'projection', 'provider', 'debug', 'capability map', '配置缺口', '契约未命中'];

fs.mkdirSync(OUTPUT, { recursive: true });

function check(value, message) { if (!value) throw new Error(message); }
function recordRoute(target) { return `/r/${target.model}/${target.record_id}?action_id=${target.action_id}&menu_id=${target.menu_id}`; }
function formRoute(target, id = target.record_id) { return `/f/${target.model}/${id}?action_id=${target.action_id}&menu_id=${target.menu_id}`; }
function listRoute(target) { return `/a/${target.action_id}?menu_id=${target.menu_id}`; }

const ALL_CASES = [
  { key: 'finance_home', role: 'demo_role_finance', route: '/' },
  { key: 'project_member_home', role: 'demo_role_project_a_member', route: '/' },
  { key: 'my_work', role: 'demo_role_finance', pageKind: 'workbench', expectedWidthMode: 'data', route: '/my-work' },
  { key: 'project_list', role: 'demo_role_pm', pageKind: 'list', expectedWidthMode: 'data', route: () => listRoute(TARGETS.project) },
  { key: 'contract_list', role: 'demo_role_pm', pageKind: 'list', expectedWidthMode: 'data', route: () => listRoute(TARGETS.contract) },
  { key: 'payment_request_list', role: 'demo_role_finance', pageKind: 'list', expectedWidthMode: 'data', route: () => listRoute(TARGETS.payment_request) },
  { key: 'payment_execution_list', role: 'demo_role_finance', pageKind: 'list', expectedWidthMode: 'data', route: () => listRoute(TARGETS.payment_execution) },
  { key: 'contract_detail', role: 'demo_role_pm', pageKind: 'detail', expectedWidthMode: 'standard', route: () => recordRoute(TARGETS.contract) },
  { key: 'settlement_detail', role: 'demo_role_finance', pageKind: 'detail', expectedWidthMode: 'standard', route: () => recordRoute(TARGETS.settlement) },
  { key: 'payment_request_detail', role: 'demo_role_finance', pageKind: 'detail', expectedWidthMode: 'standard', route: () => recordRoute(TARGETS.payment_request) },
  { key: 'payment_execution_detail', role: 'demo_role_finance', route: () => recordRoute(TARGETS.payment_execution) },
  { key: 'contract_form', role: 'demo_role_pm', pageKind: 'edit', expectedWidthMode: 'standard', route: () => formRoute(TARGETS.contract) },
  { key: 'payment_request_create', role: 'demo_role_finance', pageKind: 'create', expectedWidthMode: 'focused', mode: 'create', route: () => recordRoute(TARGETS.work_settlement) },
  { key: 'payment_request_edit', role: 'demo_role_finance', route: () => formRoute(TARGETS.payment_request) },
  { key: 'contract_create', role: 'demo_role_pm', pageKind: 'create', route: () => formRoute(TARGETS.contract, 'new') },
  { key: 'relationship_form', role: 'demo_role_finance', pageKind: 'edit', route: () => formRoute(TARGETS.payment_request) },
  { key: 'x2many_form', role: 'demo_role_pm', pageKind: 'edit', route: () => formRoute(TARGETS.contract) },
  { key: 'long_text_form', role: 'demo_role_pm', pageKind: 'edit', route: () => formRoute(TARGETS.contract) },
  { key: 'permission_denied', role: 'demo_role_project_a_member', mode: 'denied', route: () => recordRoute(TARGETS.payment_request) },
  { key: 'not_found', role: 'demo_role_finance', mode: 'not-found', route: () => `/r/${TARGETS.payment_request.model}/999999?action_id=${TARGETS.payment_request.action_id}&menu_id=${TARGETS.payment_request.menu_id}` },
  { key: 'conflict', role: 'demo_role_finance', mode: 'conflict', route: () => recordRoute(TARGETS.payment_request) },
  { key: 'empty_list', role: 'demo_role_finance', mode: 'empty', route: () => listRoute(TARGETS.payment_request) },
  { key: 'network_error', role: 'demo_role_finance', mode: 'network', route: () => recordRoute(TARGETS.payment_request) },
];
const WIDTH_CASE_KEYS = new Set(['project_list', 'contract_list', 'payment_request_list', 'payment_execution_list', 'contract_detail', 'settlement_detail', 'payment_request_detail', 'contract_form', 'payment_request_create', 'my_work']);
const WORKSPACE_CASE_KEYS = new Set(['payment_request_list', 'contract_list', 'payment_execution_list', 'contract_detail', 'settlement_detail', 'payment_request_detail', 'contract_form', 'payment_request_create']);
const WORKSPACE_COMPAT_CASE_KEYS = new Set(['payment_request_list', 'contract_detail', 'contract_form', 'payment_request_create']);
const FORM_CANVAS_CASE_KEYS = new Set(['payment_request_create', 'payment_request_edit', 'contract_create', 'contract_form', 'contract_detail', 'relationship_form', 'x2many_form', 'long_text_form']);
const CASE_FILTER = String(process.env.FE_PRO_04_CASE || process.env.FE_PRO_04W_CASE || process.env.FE_PRO_04WR_CASE || process.env.FE_PRO_04WR2_CASE || '').trim();
const PROFILE_CASES = FORM_CANVAS_AUDIT
  ? ALL_CASES.filter((entry) => FORM_CANVAS_CASE_KEYS.has(entry.key))
  : WORKSPACE_COMPAT_AUDIT
  ? ALL_CASES.filter((entry) => WORKSPACE_COMPAT_CASE_KEYS.has(entry.key))
  : WORKSPACE_AUDIT
  ? ALL_CASES.filter((entry) => WORKSPACE_CASE_KEYS.has(entry.key))
  : (WIDTH_AUDIT ? ALL_CASES.filter((entry) => WIDTH_CASE_KEYS.has(entry.key)) : ALL_CASES);
const CASES = CASE_FILTER ? PROFILE_CASES.filter((entry) => entry.key === CASE_FILTER) : PROFILE_CASES;
check(CASES.length > 0, `unknown FE_PRO_04_CASE=${CASE_FILTER}`);
const DARK_ONLY_CASES = FORM_CANVAS_AUDIT
  ? [
      { key: 'required_error', role: 'demo_role_finance', pageKind: 'create', mode: 'required-error', route: () => recordRoute(TARGETS.work_settlement) },
      { key: 'conflict', role: 'demo_role_finance', pageKind: 'detail', mode: 'conflict', route: () => recordRoute(TARGETS.payment_request) },
      { key: 'relationship_dialog', role: 'demo_role_pm', pageKind: 'create', mode: 'relation-dialog', route: () => formRoute(TARGETS.contract, 'new') },
    ]
  : WORKSPACE_AUDIT
  ? [{ key: 'permission_denied', role: 'demo_role_project_a_member', mode: 'denied', route: () => recordRoute(TARGETS.payment_request) }]
  : [{ key: 'approval_dialog', role: 'demo_role_finance', mode: 'dialog', route: () => recordRoute(TARGETS.journey_request) }];

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
  if (['create', 'required-error'].includes(entry.mode)) {
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
  if (FORM_CANVAS_AUDIT && entry.pageKind !== 'detail') {
    await page.locator('[data-form-canvas]').first().waitFor({ state: 'visible', timeout: 45000 });
  }
  if (entry.mode === 'required-error') {
    const required = page.locator('[data-form-canvas] [data-field-key] input[type="number"][aria-required="true"]:visible').first();
    await required.waitFor({ state: 'visible', timeout: 15000 });
    await required.fill('');
    await page.locator('[data-product-page-mode="form"] button').filter({ hasText: /保存|创建/ }).first().click();
    await page.locator('[data-form-error-summary], [role="alert"]').first().waitFor({ state: 'visible', timeout: 15000 });
  }
  if (entry.mode === 'relation-dialog') {
    const relationInput = page.locator('[data-form-canvas] .many2one-combobox input:visible').first();
    await relationInput.waitFor({ state: 'visible', timeout: 15000 });
    await relationInput.focus();
    await page.locator('.many2one-action:visible').filter({ hasText: /搜索更多/ }).first().click();
    await page.locator('.relation-dialog').waitFor({ state: 'visible', timeout: 15000 });
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
    const compact = await page.evaluate(() => {
      const visible = (node) => {
        const style = window.getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
      };
      return {
        title: document.querySelector('h1')?.textContent?.trim() || '',
        h1_count: document.querySelectorAll('h1').length,
        main_count: document.querySelectorAll('main').length,
        desktop_record_table_visible: [...document.querySelectorAll('.desktop-record-table')].filter(visible).length,
        horizontal_overflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
      };
    });
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
      desktop_record_table_visible: [...document.querySelectorAll('.desktop-record-table')].filter(visible).length,
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

async function pageWidthMetrics(page) {
  return page.evaluate(() => {
    const rectOf = (node) => node?.getBoundingClientRect() || null;
    const visible = (node) => {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    };
    const sidebar = [...document.querySelectorAll('#primary-sidebar, .sidebar-nav')].find(visible) || null;
    const main = document.querySelector('#main-content.router-host, main.router-host');
    const directFrame = main ? [...main.children].find((node) => visible(node) && (
      node.hasAttribute('data-page-width-mode')
      || node.hasAttribute('data-product-page-mode')
      || node.classList.contains('my-work-page')
    )) : null;
    const frame = directFrame || (main ? [...main.querySelectorAll('[data-page-width-mode], [data-product-page-mode], .my-work-page')].find(visible) : null);
    const table = main ? [...main.querySelectorAll('.table, .sc-data-table__scroll, .data-table')].find(visible) : null;
    const mainRect = rectOf(main);
    const frameRect = rectOf(frame);
    const frameStyle = frame ? window.getComputedStyle(frame) : null;
    const paddingLeft = frameStyle ? Number.parseFloat(frameStyle.paddingLeft) || 0 : 0;
    const paddingRight = frameStyle ? Number.parseFloat(frameStyle.paddingRight) || 0 : 0;
    const mainWidth = mainRect?.width || 0;
    const frameWidth = frameRect?.width || 0;
    return {
      viewport_width: window.innerWidth,
      sidebar_width: Math.round(rectOf(sidebar)?.width || 0),
      main_width: Math.round(mainWidth),
      frame_width: Math.round(frameWidth),
      content_width: Math.round(Math.max(0, frameWidth - paddingLeft - paddingRight)),
      left_blank_width: Math.round(frameRect && mainRect ? frameRect.left - mainRect.left : 0),
      right_blank_width: Math.round(frameRect && mainRect ? mainRect.right - frameRect.right : 0),
      utilization_ratio: mainWidth > 0 ? Number((frameWidth / mainWidth).toFixed(4)) : 0,
      table_client_width: table?.clientWidth || 0,
      table_scroll_width: table?.scrollWidth || 0,
      local_scroll: Boolean(table && table.scrollWidth > table.clientWidth + 1),
      page_overflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
      width_mode: frame?.getAttribute('data-page-width-mode') || 'legacy',
    };
  });
}

async function workspaceDomMetrics(page) {
  return page.evaluate(() => {
    const visible = (node) => {
      if (!(node instanceof HTMLElement)) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    };
    const firstVisible = (selectors, root = document) => {
      for (const selector of selectors) {
        const node = [...root.querySelectorAll(selector)].find(visible);
        if (node) return node;
      }
      return null;
    };
    const measure = (node) => {
      if (!node) return null;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return {
        selector: node.id ? `#${node.id}` : `.${[...node.classList].slice(0, 3).join('.')}`,
        x: Number(rect.x.toFixed(2)),
        right: Number(rect.right.toFixed(2)),
        width: Number(rect.width.toFixed(2)),
        max_width: style.maxWidth,
        padding_left: style.paddingLeft,
        padding_right: style.paddingRight,
        margin_left: style.marginLeft,
        margin_right: style.marginRight,
        overflow_x: style.overflowX,
        scroll_width: node.scrollWidth,
        client_width: node.clientWidth,
      };
    };
    const router = document.querySelector('#main-content.router-host, main.router-host');
    const directFrame = router
      ? [...router.children].find((node) => visible(node) && (node.hasAttribute('data-page-width-mode') || node.hasAttribute('data-workspace-frame') || node.hasAttribute('data-product-page-mode')))
      : null;
    const frame = directFrame || firstVisible(['[data-workspace-frame]', '[data-page-width-mode]', '[data-product-page-mode]'], router || document);
    const elements = {
      app_shell_main_region: router,
      router_host: router,
      outer_page_frame: frame,
      page_header: firstVisible(['[data-workspace-page-header]', '.sc-page-header', '.product-record-header', '.list-header', '.record-header'], frame || router || document),
      primary_action_bar: firstVisible(['[data-workspace-action-bar]', '.sc-action-bar', '.record-action-bar', '.header-actions', '.action-toolbar'], frame || router || document),
      main_content_surface: firstVisible(['[data-workspace-primary-content]', '.list-page', '.contract-form-native-shell > .card', '.record-content', '.card'], frame || router || document),
      list_toolbar: firstVisible(['.list-header-toolbar', '.action-toolbar', '.list-toolbar'], frame || router || document),
      list_table_wrapper: firstVisible(['.table', '.sc-data-table__scroll', '.data-table'], frame || router || document),
      actual_table: firstVisible(['.table table', '.sc-data-table__scroll table', 'table'], frame || router || document),
      form_header: firstVisible(['.product-record-header', '.record-header', '.contract-header', '[data-workspace-page-header]'], frame || router || document),
      form_error_summary: firstVisible(['.product-form-error-summary', '.sc-error-summary', '[role="alert"]'], frame || router || document),
      form_canvas: firstVisible(['[data-form-canvas]', '.native-form-tree', '.form-canvas', '.card--flow', '.card'], frame || router || document),
      form_section: firstVisible(['.native-container--group', '.form-section', '.sc-section'], frame || router || document),
      sticky_action_bar: firstVisible(['.sticky-actions', '.sticky-action-bar', '.record-action-bar', '.sc-action-bar'], frame || router || document),
    };
    const routerRect = router?.getBoundingClientRect() || null;
    const childOverflows = router && routerRect
      ? [...router.querySelectorAll('*')]
          .filter(visible)
          .filter((node) => {
            if (window.getComputedStyle(node).position === 'fixed') return false;
            const scrollOwner = node.closest('.table, .sc-data-table__scroll, .data-table, .sc-table-shell');
            if (!scrollOwner || scrollOwner === node) return true;
            const overflow = window.getComputedStyle(scrollOwner).overflowX;
            return overflow !== 'auto' && overflow !== 'scroll';
          })
          .map((node) => {
            const rect = node.getBoundingClientRect();
            return {
              node,
              left: Math.max(0, routerRect.left - rect.left),
              right: Math.max(0, rect.right - routerRect.right),
            };
          })
          .filter((row) => row.left > 1 || row.right > 1)
          .map((row) => ({
            selector: row.node.id ? `#${row.node.id}` : `.${[...row.node.classList].slice(0, 3).join('.')}`,
            left: Number(row.left.toFixed(2)),
            right: Number(row.right.toFixed(2)),
          }))
      : [];
    const measured = Object.fromEntries(Object.entries(elements).map(([key, node]) => [key, measure(node)]));
    const tableWrapper = measured.list_table_wrapper;
    const actualTable = measured.actual_table;
    return {
      dom: measured,
      router_child_overflow_count: childOverflows.length,
      router_child_overflow_max: childOverflows.reduce((max, row) => Math.max(max, row.left, row.right), 0),
      router_child_overflow_sample: childOverflows.slice(0, 20),
      table_utilization_ratio: tableWrapper && actualTable && tableWrapper.client_width > 0
        ? Number((actualTable.width / tableWrapper.client_width).toFixed(4))
        : null,
    };
  });
}

async function formCanvasMetrics(page) {
  return page.evaluate(() => {
    const visible = (node) => {
      if (!(node instanceof HTMLElement)) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    };
    const first = (selector) => [...document.querySelectorAll(selector)].find(visible) || null;
    const rect = (node) => node?.getBoundingClientRect() || null;
    const primary = first('[data-workspace-primary-content]');
    const canvas = first('[data-form-canvas]');
    const sections = [...document.querySelectorAll('[data-form-canvas] .native-container--group, [data-form-canvas] .template-form-section')].filter(visible);
    const grids = [...document.querySelectorAll('[data-form-canvas] .template-form-section-grid')].filter(visible);
    const fields = [...document.querySelectorAll('[data-form-canvas] .template-form-section-grid > .field')].filter(visible);
    const primaryRect = rect(primary);
    const canvasRect = rect(canvas);
    const primaryStyle = primary ? window.getComputedStyle(primary) : null;
    const canvasStyle = canvas ? window.getComputedStyle(canvas) : null;
    const primaryPaddingLeft = Number.parseFloat(primaryStyle?.paddingLeft || '0') || 0;
    const primaryPaddingRight = Number.parseFloat(primaryStyle?.paddingRight || '0') || 0;
    const canvasPaddingLeft = Number.parseFloat(canvasStyle?.paddingLeft || '0') || 0;
    const canvasPaddingRight = Number.parseFloat(canvasStyle?.paddingRight || '0') || 0;
    const sectionWidths = sections.map((node) => rect(node)?.width || 0).filter(Boolean);
    const gridWidths = grids.map((node) => rect(node)?.width || 0).filter(Boolean);
    const columnCounts = grids.map((node) => {
      const columns = window.getComputedStyle(node).gridTemplateColumns;
      return columns && columns !== 'none' ? columns.split(/\s+/).filter(Boolean).length : 0;
    }).filter(Boolean);
    const normalFields = fields.filter((node) => !node.classList.contains('field--full') && !node.classList.contains('field--wide'));
    const normalWidths = normalFields.map((node) => rect(node)?.width || 0).filter(Boolean);
    const controls = [...document.querySelectorAll('[data-form-canvas] .field :is(input, select, textarea)')].filter(visible);
    const controlWidths = controls.map((node) => rect(node)?.width || 0).filter(Boolean);
    const canvasWidth = canvasRect?.width || 0;
    const primaryWidth = primaryRect?.width || 0;
    const primaryAvailableWidth = Math.max(0, primaryWidth - primaryPaddingLeft - primaryPaddingRight);
    const canvasAvailableWidth = Math.max(0, canvasWidth - canvasPaddingLeft - canvasPaddingRight);
    return {
      form_canvas_width: Number(canvasWidth.toFixed(2)),
      primary_content_width: Number(primaryWidth.toFixed(2)),
      primary_available_width: Number(primaryAvailableWidth.toFixed(2)),
      canvas_utilization_ratio: primaryAvailableWidth ? Number((canvasWidth / primaryAvailableWidth).toFixed(4)) : null,
      form_section_min_width: sectionWidths.length ? Number(Math.min(...sectionWidths).toFixed(2)) : null,
      form_section_utilization_ratio: canvasAvailableWidth && sectionWidths.length ? Number((Math.min(...sectionWidths) / canvasAvailableWidth).toFixed(4)) : null,
      field_grid_min_width: gridWidths.length ? Number(Math.min(...gridWidths).toFixed(2)) : null,
      field_column_counts: [...new Set(columnCounts)].sort((a, b) => a - b),
      max_normal_field_wrapper_width: normalWidths.length ? Number(Math.max(...normalWidths).toFixed(2)) : null,
      max_input_control_width: controlWidths.length ? Number(Math.max(...controlWidths).toFixed(2)) : null,
      full_span_field_count: fields.filter((node) => node.classList.contains('field--full')).length,
      wide_span_field_count: fields.filter((node) => node.classList.contains('field--wide')).length,
      relation_field_count: fields.filter((node) => node.querySelector('.many2one-widget-shell, .relation-field')).length,
      x2many_field_count: fields.filter((node) => node.querySelector('.x2many-relation, .x2many-field, table')).length,
      right_unused_space: primaryRect && canvasRect ? Number(Math.max(0, primaryRect.right - primaryPaddingRight - canvasRect.right).toFixed(2)) : null,
      error_summary_width: Number((rect(first('[data-form-error-summary], .product-form-error-summary'))?.width || 0).toFixed(2)),
      action_bar_width: Number((rect(first('[data-workspace-action-bar], .record-action-bar, .sc-action-bar'))?.width || 0).toFixed(2)),
    };
  });
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
  const viewports = theme === 'dark'
    ? (WORKSPACE_AUDIT
        ? [{ width: 1920, height: 1080 }]
        : (WIDTH_AUDIT
            ? (entry.key === 'contract_list'
                ? [{ width: 1920, height: 1080 }, { width: 390, height: 844 }]
                : [{ width: 1920, height: 1080 }])
            : [{ width: 1440, height: 900 }]))
    : (WORKSPACE_COMPAT_AUDIT && ['contract_detail', 'contract_form'].includes(entry.key)
        ? VIEWPORTS.filter((viewport) => viewport.width === 1920)
        : VIEWPORTS);
  const scenarios = viewports.map((viewport) => ({ viewport, sidebarState: 'expanded' }));
  if (WORKSPACE_AUDIT && !WORKSPACE_COMPAT_AUDIT && PHASE === 'final' && theme === 'light') {
    scenarios.push({ viewport: { width: 1920, height: 1080 }, sidebarState: 'collapsed' });
  }
  let sidebarState = 'expanded';
  for (const scenario of scenarios) {
    const { viewport } = scenario;
    console.log(`[fe-pro-04] ${entry.key}:${theme}:${viewport.width}x${viewport.height}:${scenario.sidebarState}`);
    const viewportStarted = Date.now();
    await page.setViewportSize(viewport);
    await page.waitForTimeout(120);
    if (scenario.sidebarState !== sidebarState && viewport.width > 900) {
      await page.getByRole('button', { name: scenario.sidebarState === 'collapsed' ? '隐藏侧边栏' : '显示侧边栏' }).click();
      await page.waitForTimeout(120);
      sidebarState = scenario.sidebarState;
    }
    const screenshot = path.join(OUTPUT, `${entry.key}-${theme}-${viewport.width}x${viewport.height}-${scenario.sidebarState}.png`);
    await page.screenshot({ path: screenshot, fullPage: false, timeout: 5000 });
    console.log(`[fe-pro-04] ${entry.key}:${theme}:${viewport.width}x${viewport.height}:captured_ms=${Date.now() - viewportStarted}`);
    rows.push({
      surface: entry.key,
      role: entry.role,
      page_kind: entry.pageKind || 'other',
      expected_width_mode: entry.expectedWidthMode || 'standard',
      company,
      viewport: `${viewport.width}x${viewport.height}`,
      sidebar_state: scenario.sidebarState,
      theme,
      route: new URL(page.url()).pathname,
      component_contract_version: 'sc-product-design-system.v1',
      screenshot,
      screenshot_sha256: '',
      accessibility_scanned: viewport.width === 1440,
      ...(await visualMetrics(page, viewport.width === 1440)),
      ...(await pageWidthMetrics(page)),
      ...(WORKSPACE_AUDIT ? await workspaceDomMetrics(page) : {}),
      ...(FORM_CANVAS_AUDIT ? await formCanvasMetrics(page) : {}),
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
    if (PHASE === 'final' && !WORKSPACE_COMPAT_AUDIT && (WORKSPACE_AUDIT || !WIDTH_AUDIT)) {
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
      schema_version: FORM_CANVAS_AUDIT
        ? 'frontend_form_canvas_wide_grid_audit.v1'
        : WORKSPACE_COMPAT_AUDIT
        ? 'frontend_workspace_layout_contract_compatibility_audit.v1'
        : WORKSPACE_AUDIT
        ? 'frontend_workspace_content_alignment_audit.v1'
        : (WIDTH_AUDIT ? 'frontend_page_width_audit.v1' : 'frontend_product_design_system_audit.v1'),
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
    if (WORKSPACE_AUDIT && PHASE === 'baseline') {
      fs.writeFileSync(path.join(ROOT, 'baseline-dom.json'), `${JSON.stringify(report, null, 2)}\n`);
    }
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
      const expectedLightRows = FORM_CANVAS_AUDIT
        ? CASES.length * (VIEWPORTS.length + 1)
        : WORKSPACE_COMPAT_AUDIT
        ? CASES.reduce((count, entry) => count + (['contract_detail', 'contract_form'].includes(entry.key) ? 1 : 2), 0)
        : WORKSPACE_AUDIT
        ? CASES.length * (VIEWPORTS.length + 1)
        : CASES.length * VIEWPORTS.length;
      check(pages.filter((row) => row.theme === 'light').length === expectedLightRows, 'light visual matrix incomplete');
      const expectedDarkRows = WORKSPACE_COMPAT_AUDIT
        ? 0
        : CASES.filter((entry) => DARK_CASES.has(entry.key)).length
          + ((WORKSPACE_AUDIT || !WIDTH_AUDIT) ? DARK_ONLY_CASES.length : 0);
      check(pages.filter((row) => row.theme === 'dark').length === expectedDarkRows, 'dark visual sample incomplete');
      check(!pages.some((row) => row.h1_count !== 1 || row.main_count !== 1), 'page landmark hierarchy failed');
      check(!pages.some((row) => row.font_level_count > 4), 'page typography hierarchy exceeds four visible levels');
      check(!pages.some((row) => row.viewport === '390x844' && row.desktop_record_table_visible > 0), 'desktop record table leaked into mobile layout');
      check(!pages.some((row) => row.horizontal_overflow > 1 || row.axe_critical_serious.length), 'responsive/accessibility visual guard failed');
      check(!pages.some((row) => row.technical_term_hits.length), 'technical product wording found');
      check(!runtime.some((row) => row.console.length || row.pageerror.length || row.http.length), 'unexpected runtime errors found');
      if (WORKSPACE_AUDIT) {
        const lightRows = pages.filter((row) => row.theme === 'light');
        const aligned = (rows, path) => {
          const values = rows.map((row) => path.split('.').reduce((value, key) => value?.[key], row)).filter((value) => typeof value === 'number');
          return values.length === rows.length && Math.max(...values) - Math.min(...values) <= 1;
        };
        const groups = new Map();
        for (const row of lightRows) {
          const key = `${row.viewport}:${row.sidebar_state}`;
          groups.set(key, [...(groups.get(key) || []), row]);
        }
        for (const [key, rows] of groups) {
          check(aligned(rows, 'dom.outer_page_frame.x') && aligned(rows, 'dom.outer_page_frame.right'), `workspace frame alignment failed: ${key}`);
          check(aligned(rows, 'dom.page_header.x') && aligned(rows, 'dom.page_header.right'), `page header alignment failed: ${key}`);
          check(aligned(rows, 'dom.main_content_surface.x') && aligned(rows, 'dom.main_content_surface.right'), `primary content alignment failed: ${key}`);
        }
        check(!lightRows.some((row) => row.viewport_width === 1920 && row.utilization_ratio < 0.98), '1920 workspace utilization below 98%');
        check(!lightRows.some((row) => row.viewport_width === 2560 && row.frame_width > 1921), 'workspace frame exceeded 1920px');
        check(!lightRows.some((row) => row.page_overflow > 1 || row.router_child_overflow_count > 0), 'document or router child overflow found');
        check(!lightRows.some((row) => row.table_utilization_ratio !== null && row.table_utilization_ratio < 0.98), 'table utilization below 98%');
        if (FORM_CANVAS_AUDIT) {
          const formRows = lightRows.filter((row) => row.form_canvas_width > 0);
          check(!formRows.some((row) => row.canvas_utilization_ratio < (row.viewport_width === 390 ? 0.98 : 0.95)), 'form canvas utilization below threshold');
          check(!formRows.some((row) => row.viewport_width >= 1440 && row.form_section_utilization_ratio < 0.95), 'desktop form section utilization below 95%');
          check(!formRows.some((row) => row.max_normal_field_wrapper_width > 720), 'normal field wrapper exceeded 720px');
          check(!formRows.some((row) => row.viewport_width === 390 && (row.field_column_counts.length !== 1 || row.field_column_counts[0] !== 1)), 'mobile form grid is not single-column');
        }
      } else if (WIDTH_AUDIT) {
        const lightRows = pages.filter((row) => row.theme === 'light');
        check(!lightRows.some((row) => row.width_mode !== row.expected_width_mode), 'page width mode contract mismatch');
        check(!lightRows.some((row) => row.viewport_width === 1920 && row.width_mode === 'data' && row.utilization_ratio < 0.94), '1920 data-page utilization below 94%');
        check(!lightRows.some((row) => row.width_mode === 'standard' && row.frame_width > 1441), 'standard page exceeded 1440px');
        check(!lightRows.some((row) => row.width_mode === 'focused' && row.frame_width > 1081), 'focused page exceeded 1080px');
        check(!lightRows.some((row) => row.viewport_width === 2560 && row.width_mode === 'data' && row.frame_width > 1921), 'data page exceeded 1920px');
        check(!lightRows.some((row) => row.page_overflow > 1), 'page-level horizontal overflow found');
      }
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
