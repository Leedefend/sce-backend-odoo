#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { launchChromium } from './playwright_runtime.mjs';

const require = createRequire(import.meta.url);
const axeModule = require(require.resolve('@axe-core/playwright', { paths: [path.resolve('frontend/apps/web/node_modules')] }));
const AxeBuilder = axeModule.default || axeModule;

const BASE_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const DB_NAME = process.env.DB_NAME || 'sc_frontend_acceptance';
const PASSWORD = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const PHASE = process.env.FE_PRO_03_PHASE === 'final' ? 'final' : 'baseline';
const ROOT = process.env.FE_PRO_03_ARTIFACT_ROOT || 'artifacts/frontend-professional/fe-pro-03';
const OUTPUT = path.join(ROOT, PHASE);
const REPORT = path.join(ROOT, `${PHASE}-report.json`);
const TARGETS = JSON.parse(process.env.FRONTEND_FINANCIAL_WORKSPACE_TARGETS_JSON || '{}');
const VIEWPORTS = [
  { width: 1440, height: 900 },
  { width: 1280, height: 800 },
  ...(PHASE === 'final' ? [{ width: 768, height: 1024 }] : []),
  { width: 390, height: 844 },
];
const ALL_CASES = [
  { key: 'project_detail', role: 'demo_role_pm', target: 'project', mode: 'record', expected: 'FE Project A' },
  { key: 'contract_detail', role: 'demo_role_pm', target: 'contract', mode: 'record', expected: 'CONOUT2600001' },
  { key: 'settlement_detail', role: 'demo_role_finance', target: 'settlement', mode: 'record', expected: 'FE-A-SET-001' },
  { key: 'payment_request_detail', role: 'demo_role_finance', target: 'payment_request', mode: 'record', expected: 'FE-A-PR-001' },
  { key: 'payment_execution_detail', role: 'demo_role_finance', target: 'payment_execution', mode: 'record', expected: 'FE-A-PE-001' },
  { key: 'contract_edit', role: 'demo_role_pm', target: 'contract', mode: 'form', expected: 'CONOUT2600001' },
  { key: 'payment_request_create', role: 'demo_role_finance', target: 'payment_request', mode: 'create', expected: '新建' },
  { key: 'payment_request_edit', role: 'demo_role_finance', target: 'payment_request', mode: 'form', expected: 'FE-A-PR-001' },
];
const CASE_FILTER = String(process.env.FE_PRO_03_CASE || '').trim();
const CASES = CASE_FILTER ? ALL_CASES.filter((entry) => entry.key === CASE_FILTER) : ALL_CASES;
check(CASES.length > 0, `unknown FE_PRO_03_CASE=${CASE_FILTER}`);

fs.mkdirSync(OUTPUT, { recursive: true });

function check(value, message) {
  if (!value) throw new Error(message);
}

function routeFor(entry) {
  const target = TARGETS[entry.target];
  check(target?.record_id > 0 && target?.action_id > 0 && target?.menu_id > 0, `missing target ${entry.target}`);
  const prefix = entry.mode === 'record' ? 'r' : 'f';
  const id = entry.mode === 'create' ? 'new' : target.record_id;
  return `/${prefix}/${encodeURIComponent(target.model)}/${id}?action_id=${target.action_id}&menu_id=${target.menu_id}`;
}

async function openCase(page, entry) {
  if (entry.key !== 'payment_request_create') {
    await page.goto(`${BASE_URL}${routeFor(entry)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    return;
  }
  const settlement = TARGETS.settlement;
  check(
    settlement?.record_id > 0 && settlement?.action_id > 0 && settlement?.menu_id > 0,
    'missing legal payment request create entry settlement',
  );
  await page.goto(`${BASE_URL}${routeFor({ target: 'settlement', mode: 'record' })}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  const workspace = page.locator('.financial-workspace[data-workspace-kind="settlement"]');
  try {
    await workspace.waitFor({ timeout: 45000 });
  } catch (error) {
    throw new Error(`legal create settlement unavailable; url=${page.url()} body=${(await page.locator('body').innerText()).slice(0, 1800)} cause=${error.message}`);
  }
  await workspace.getByRole('button', { name: '新建付款申请', exact: true }).click();
  await page.waitForURL((url) => url.pathname.includes('/f/payment.request/new'), { timeout: 45000 });
}

function captureRuntime(page) {
  const runtime = { console: [], pageerror: [], http: [], requests: [] };
  page.on('console', (message) => {
    if (message.type() === 'error' && !/favicon|ResizeObserver/i.test(message.text())) runtime.console.push(message.text());
  });
  page.on('pageerror', (error) => runtime.pageerror.push(error.message));
  page.on('response', (response) => {
    if (response.status() >= 400) runtime.http.push({ status: response.status(), url: response.url() });
  });
  page.on('request', (request) => {
    if (request.method() === 'POST' && request.url().includes('/api/')) runtime.requests.push(request.url());
  });
  return runtime;
}

async function login(page, loginName) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('#login-username, input[autocomplete="username"]').first().fill(loginName);
  await page.locator('#login-password, input[autocomplete="current-password"]').first().fill(PASSWORD);
  const database = page.locator('input').nth(2);
  if (await database.isEnabled().catch(() => false)) await database.fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
}

async function waitForRecordSurface(page, entry) {
  await page.locator('[data-product-page-mode="form"]').waitFor({ timeout: 45000 });
  await page.waitForFunction((expectedIdentity) => {
    const main = document.querySelector('main');
    const text = main?.textContent || '';
    return Boolean(main)
      && !/(正在加载|正在初始化|加载中)/.test(text)
      && (!expectedIdentity || text.includes(expectedIdentity));
  }, entry.expected, { timeout: 45000 });
  await page.waitForTimeout(250);
}

async function pageMetrics(page, startedAt) {
  const surface = page.locator('[data-product-page-mode="form"]:visible').first();
  const surfaceText = await surface.innerText();
  const heading = page.locator('h1:visible').first();
  const state = page.locator('.financial-workspace__status:visible, .native-statusbar:visible, [data-product-record-status]:visible').first();
  const amount = page.locator('[data-fact-key]:visible .financial-workspace__money, [data-fact-key*="amount"]:visible, [data-product-money-fact]:visible').first();
  const relation = page.locator('[data-relation-key]:visible, [data-product-relationship]:visible').first();
  const stateVisible = await state.isVisible().catch(() => false);
  const amountVisible = await amount.isVisible().catch(() => false);
  const relationVisible = await relation.isVisible().catch(() => false);
  const dimensions = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    scrollHeight: document.documentElement.scrollHeight,
  }));
  const firstScreenActions = await surface.locator('button:not(:disabled), a[href]').evaluateAll((nodes) => nodes.filter((node) => {
    const rect = node.getBoundingClientRect();
    const style = window.getComputedStyle(node);
    return rect.width > 0
      && rect.height > 0
      && rect.top < window.innerHeight
      && rect.bottom > 0
      && style.visibility !== 'hidden'
      && style.display !== 'none';
  }).length);
  const firstScreenFacts = await surface.locator('[data-fact-key], [data-product-fact]').evaluateAll((nodes) => nodes.filter((node) => {
    const rect = node.getBoundingClientRect();
    const style = window.getComputedStyle(node);
    return rect.width > 0
      && rect.height > 0
      && rect.top < window.innerHeight
      && rect.bottom > 0
      && style.visibility !== 'hidden'
      && style.display !== 'none';
  }).length);
  const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  return {
    h1_count: await page.locator('h1:visible').count(),
    heading: await heading.innerText().catch(() => ''),
    business_title: !/(?:project\.project|construction\.contract|sc\.settlement\.order|payment\.request|sc\.payment\.execution)\s*#?\s*\d+/i.test(surfaceText),
    technical_title_fallback: (surfaceText.match(/(?:project\.project|construction\.contract|sc\.settlement\.order|payment\.request|sc\.payment\.execution)\s*#?\s*\d+/gi) || []),
    first_screen_facts: firstScreenFacts,
    first_screen_actions: firstScreenActions,
    state_visible: stateVisible,
    amount_visible: amountVisible,
    relationship_visible: relationVisible,
    state_find_ms: stateVisible ? Date.now() - startedAt : null,
    amount_find_ms: amountVisible ? Date.now() - startedAt : null,
    relationship_find_ms: relationVisible ? Date.now() - startedAt : null,
    relationship_clicks: relationVisible ? 1 : null,
    page_height: dimensions.scrollHeight,
    horizontal_overflow: Math.max(0, dimensions.scrollWidth - dimensions.clientWidth),
    axe_critical_serious: axe.violations.filter((row) => ['critical', 'serious'].includes(row.impact)).map((row) => ({
      id: row.id,
      impact: row.impact,
      nodes: row.nodes.length,
    })),
  };
}

async function validationProbe(page) {
  const required = page.locator('[data-product-page-mode="form"]:visible [data-field-key] input[type="number"][aria-required="true"]:visible').first();
  if (!(await required.isVisible().catch(() => false))) return { status: 'FAIL', reason: 'required money control not discoverable', elapsed_ms: null };
  const fieldKey = await required.locator('xpath=ancestor::*[@data-field-key][1]').getAttribute('data-field-key');
  const describedByBefore = await required.getAttribute('aria-describedby');
  const original = await required.inputValue().catch(() => '');
  await required.fill('').catch(() => {});
  const started = Date.now();
  const save = page.locator('[data-product-page-mode="form"]:visible button').filter({ hasText: /保存|创建/ }).first();
  if (!(await save.isVisible().catch(() => false))) return { status: 'NO_SAVE_ACTION', elapsed_ms: null };
  await save.click();
  const error = page.locator('[role="alert"], .validation-error, [aria-invalid="true"]').first();
  await error.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
  const visible = await error.isVisible().catch(() => false);
  const invalid = await required.getAttribute('aria-invalid');
  const describedBy = await required.getAttribute('aria-describedby');
  const describedNodes = describedBy ? await page.locator(describedBy.split(/\s+/).map((id) => `#${id}`).join(',')).count() : 0;
  const focused = await required.evaluate((node) => document.activeElement === node).catch(() => false);
  if (original) await required.fill(original).catch(() => {});
  const passed = visible && invalid === 'true' && describedNodes > 0 && focused;
  return {
    status: passed ? 'PASS' : 'FAIL',
    field_key: fieldKey,
    aria_required: await required.getAttribute('aria-required'),
    aria_invalid: invalid,
    aria_describedby_before: describedByBefore,
    aria_describedby_after: describedBy,
    described_nodes: describedNodes,
    focused,
    elapsed_ms: visible ? Date.now() - started : null,
  };
}

async function captureCase(browser, entry) {
  const context = await browser.newContext({ viewport: VIEWPORTS[0], locale: 'zh-CN' });
  const page = await context.newPage();
  const runtime = captureRuntime(page);
  await login(page, entry.role);
  const started = Date.now();
  await openCase(page, entry);
  await waitForRecordSurface(page, entry);
  const rows = [];
  for (const viewport of VIEWPORTS) {
    await page.setViewportSize(viewport);
    await page.waitForTimeout(150);
    const metrics = await pageMetrics(page, started);
    const screenshot = path.join(OUTPUT, `${entry.key}-${viewport.width}x${viewport.height}.png`);
    await page.screenshot({ path: screenshot, fullPage: true });
    rows.push({
      page: entry.key,
      role: entry.role,
      viewport: `${viewport.width}x${viewport.height}`,
      route: new URL(page.url()).pathname,
      expected_identity: entry.expected,
      ...metrics,
      screenshot,
    });
  }
  const validation = entry.key === 'payment_request_create' ? await validationProbe(page) : null;
  await context.close();
  return { rows, validation, runtime };
}

async function main() {
  const browser = await launchChromium({ headless: true });
  try {
    const pages = [];
    const validation = [];
    for (const entry of CASES) {
      const result = await captureCase(browser, entry);
      pages.push(...result.rows.map((row) => ({ ...row, runtime: result.runtime })));
      if (result.validation) validation.push({ page: entry.key, ...result.validation });
    }
    const report = {
      schema_version: 'frontend_core_record_form_professional_audit.v1',
      phase: PHASE,
      git_sha: process.env.GIT_SHA || '',
      database: DB_NAME,
      base_url: BASE_URL,
      pages,
      validation,
      source_size: {
        record_view: fs.existsSync('frontend/apps/web/src/views/RecordView.vue') ? fs.readFileSync('frontend/apps/web/src/views/RecordView.vue', 'utf8').split('\n').length - 1 : 0,
        contract_form_page: fs.readFileSync('frontend/apps/web/src/pages/ContractFormPage.vue', 'utf8').split('\n').length - 1,
        financial_relationship_workspace: fs.readFileSync('frontend/apps/web/src/components/business/FinancialRelationshipWorkspace.vue', 'utf8').split('\n').length - 1,
      },
    };
    fs.writeFileSync(REPORT, `${JSON.stringify(report, null, 2)}\n`);
    if (PHASE === 'final') {
      const baseline = JSON.parse(fs.readFileSync(path.join(ROOT, 'baseline-report.json'), 'utf8'));
      fs.writeFileSync(path.join(ROOT, 'comparison-report.json'), `${JSON.stringify({
        schema_version: 'frontend_core_record_form_professional_comparison.v1',
        baseline_sha: baseline.git_sha,
        final_sha: report.git_sha,
        source_size: { before: baseline.source_size, after: report.source_size },
        pages: report.pages.map((row) => ({
          page: row.page,
          viewport: row.viewport,
          before: baseline.pages.find((item) => item.page === row.page && item.viewport === row.viewport) || null,
          after: row,
        })),
        validation: { before: baseline.validation, after: report.validation },
      }, null, 2)}\n`);
      check(pages.length === CASES.length * VIEWPORTS.length, `expected ${CASES.length * VIEWPORTS.length} page rows`);
      check(!pages.some((row) => row.h1_count !== 1 || !row.business_title || row.technical_title_fallback.length), 'page identity guard failed');
      check(!pages.some((row) => row.first_screen_actions > 3), 'first-screen action hierarchy guard failed');
      check(!pages.some((row) => row.horizontal_overflow > 1 || row.axe_critical_serious.length), 'responsive/accessibility guard failed');
      check(!pages.some((row) => row.runtime.console.length || row.runtime.pageerror.length || row.runtime.http.length), 'runtime error guard failed');
    }
    console.log(JSON.stringify({ report: REPORT, phase: PHASE, pages: pages.length, validation }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(`[frontend_core_record_form_professional_audit] ${error.stack || error.message}`);
  process.exitCode = 2;
});
