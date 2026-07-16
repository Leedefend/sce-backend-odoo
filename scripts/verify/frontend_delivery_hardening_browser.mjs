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
const OUT = process.env.ARTIFACTS_DIR || 'artifacts/frontend-delivery-hardening';
const TARGETS = JSON.parse(process.env.FRONTEND_DELIVERY_HARDENING_TARGETS_JSON || '{}');
const SCREENSHOTS = path.join(OUT, 'screenshots');
const TRACES = path.join(OUT, 'traces');
const PERF_ONLY = process.env.DELIVERY_HARDENING_PERF_ONLY === '1';
const PERF_BASELINE_CAPTURE = process.env.DELIVERY_HARDENING_BASELINE_CAPTURE === '1';
const PERF_BASELINE_PATH = process.env.DELIVERY_HARDENING_BASELINE_JSON
  || 'docs/frontend_productization/frontend_delivery_performance_baseline_v1.json';
const PERF_RUNS = Number(process.env.DELIVERY_HARDENING_PERF_RUNS || 5);
fs.mkdirSync(SCREENSHOTS, { recursive: true });
fs.mkdirSync(TRACES, { recursive: true });

function check(value, message) { if (!value) throw new Error(message); }
function recordRoute(target) { return `/r/${target.model}/${target.record_id}?action_id=${target.action_id}&menu_id=${target.menu_id}`; }
function listRoute(target) { return `/a/${target.action_id}?menu_id=${target.menu_id}`; }
function median(values) { const rows = [...values].sort((a, b) => a - b); return rows[Math.floor(rows.length / 2)] || 0; }
function stats(values) { return { samples_ms: values, median_ms: median(values), slowest_ms: Math.max(...values, 0) }; }
async function time(run) { const start = performance.now(); await run(); return Math.round(performance.now() - start); }

function capture(page) {
  const state = {
    console: [], pageerror: [], unhandled: [], http: [], expectedHttp: [], expectedConsole: [],
    expectForbidden: false, expectedConsoleAllowance: 0, expectedRequests: new WeakSet(),
  };
  page.on('request', (request) => {
    if (!state.expectForbidden || !request.url().includes('/api/v1/intent')) return;
    try {
      const body = JSON.parse(request.postData() || '{}');
      // The denied surface may encode the target model in either the v1 or v2
      // contract shape.  The request is authoritative here: this flag is only
      // enabled while opening the deliberately forbidden responsive surface.
      if (body.intent === 'ui.contract.v2') state.expectedRequests.add(request);
    } catch {}
  });
  page.on('console', (message) => {
    if (message.type() !== 'error' || /favicon|ResizeObserver/i.test(message.text())) return;
    if (/Failed to load resource/i.test(message.text()) && state.expectedConsoleAllowance > 0) {
      state.expectedConsoleAllowance -= 1;
      state.expectedConsole.push(message.text());
      return;
    }
    state.console.push(message.text());
  });
  page.on('pageerror', (error) => state.pageerror.push(error.message));
  page.on('response', (response) => {
    if (response.status() < 400 || !response.url().includes('/api/v1/')) return;
    let intent = ''; try { intent = JSON.parse(response.request().postData() || '{}').intent || ''; } catch {}
    const row = { status: response.status(), url: response.url(), intent };
    if (
      response.status() === 403
      && intent === 'ui.contract.v2'
      && (state.expectedRequests.has(response.request()) || state.expectForbidden)
    ) {
      state.expectedHttp.push(row);
      const consoleIndex = state.console.findIndex((line) => /Failed to load resource/i.test(line));
      if (consoleIndex >= 0) state.expectedConsole.push(...state.console.splice(consoleIndex, 1));
      else state.expectedConsoleAllowance += 1;
      return;
    }
    state.http.push(row);
  });
  return state;
}
function assertRuntimeClean(state, label, allowed = []) {
  check(!state.console.length, `${label}: console=${state.console.join(' | ')} http=${JSON.stringify(state.http)}`);
  check(!state.pageerror.length, `${label}: pageerror=${state.pageerror.join(' | ')}`);
  const bad = state.http.filter((row) => !allowed.includes(row.status));
  check(!bad.length, `${label}: http=${JSON.stringify(bad)}`);
}
function resetRuntime(state) {
  state.console.length = 0; state.pageerror.length = 0; state.unhandled.length = 0; state.http.length = 0;
}
async function login(page, user, keyboard = false) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  const username = page.locator('#login-username, input[autocomplete="username"]').first();
  const password = page.locator('#login-password, input[autocomplete="current-password"]').first();
  await username.fill(user);
  await password.fill(PASSWORD);
  const db = page.locator('input').nth(2);
  if (await db.isEnabled()) await db.fill(DB_NAME);
  if (keyboard) await password.press('Enter');
  else await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
}
async function logout(page) {
  const logoutButton = page.getByRole('button', { name: '退出登录' });
  if (!(await logoutButton.isVisible().catch(() => false))) {
    const menuButton = page.getByRole('button', { name: '菜单', exact: true });
    if (await menuButton.isVisible().catch(() => false)) await menuButton.click();
  }
  await logoutButton.click();
  await page.waitForURL((url) => url.pathname.includes('/login'), { timeout: 30000 });
}
async function waitBusiness(page) {
  await page.locator('.financial-workspace, .product-work, .sc-product-main-surface, .sc-state-panel').first().waitFor({ timeout: 45000 });
}
async function open(page, route) {
  await page.goto(`${BASE_URL}${route}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitBusiness(page);
}
async function selectCompany(page, label) {
  const select = page.getByLabel('当前公司');
  const initialized = page.waitForResponse((response) => {
    if (!response.url().includes('/api/v1/intent')) return false;
    try { return JSON.parse(response.request().postData() || '{}').intent === 'system.init'; } catch { return false; }
  }, { timeout: 45000 });
  await select.selectOption({ label });
  await initialized;
  await page.waitForFunction((expected) => document.body.innerText.includes(expected), label, { timeout: 45000 });
}
async function navigateSpa(page, route, readySelector = '.sc-product-main-surface, .financial-workspace, .product-work, .sc-state-panel') {
  await page.evaluate((target) => {
    window.history.pushState({}, '', target);
    window.dispatchEvent(new PopStateEvent('popstate'));
  }, route);
  const target = new URL(route, BASE_URL);
  await page.waitForURL((url) => (
    url.pathname === target.pathname
    && [...target.searchParams.entries()].every(([key, value]) => url.searchParams.get(key) === value)
  ), { timeout: 45000 });
  // The route's stable UI is authoritative: some surfaces issue api.data while
  // others use a product intent or satisfy metadata from the initialized store.
  // Waiting for one guessed intent turns a valid navigation into a false timeout.
  await page.waitForTimeout(50);
  await page.locator(readySelector).first().waitFor({ state: 'visible', timeout: 45000 });
  await page.waitForTimeout(50);
}
async function assertNoOverflow(page, label) {
  const size = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth }));
  check(size.scroll <= size.client + 1, `${label}: overflow ${size.scroll}/${size.client}`);
}
async function axe(page, label) {
  const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  const blocking = result.violations.filter((item) => ['critical', 'serious'].includes(item.impact));
  return { label, violations: result.violations.map((item) => ({
    id: item.id,
    impact: item.impact,
    node_count: item.nodes.length,
    help: item.help,
    nodes: item.nodes.map((node) => ({ target: node.target, html: node.html, failure_summary: node.failureSummary })),
  })), blocking: blocking.length };
}
function fulfillError(route, status, code, message) {
  return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify({ error: { message, reason_code: code, retryable: true } }) });
}
async function interceptNextBusiness(page, handler, expectedTarget) {
  let used = false;
  const callback = async (route) => {
    let payload = {};
    try { payload = JSON.parse(route.request().postData() || '{}'); } catch {}
    const intent = payload.intent || '';
    const params = payload.params || {};
    const ids = Array.isArray(params.ids) ? params.ids.map(Number) : [];
    const isTargetRead = intent === 'api.data' && params.op === 'read'
      && params.model === expectedTarget.model && ids.includes(Number(expectedTarget.record_id));
    if (isTargetRead) {
      if (!used) console.log(`[delivery-hardening] injecting ${intent}:${params.op}:${params.model}:${ids.join(',')}`);
      used = true;
      await handler(route, intent);
      return;
    }
    await route.continue();
  };
  await page.route('**/api/v1/intent**', callback);
  return async () => page.unroute('**/api/v1/intent**', callback);
}

async function main() {
  for (const key of ['project', 'contract', 'settlement', 'payment_request', 'payment_execution', 'journey_request', 'work_settlement']) check(TARGETS[key]?.record_id > 0, `missing ${key}`);
  const browser = await launchChromium({ headless: true });
  const report = { git_sha: process.env.GIT_SHA || '', database: DB_NAME, base_url: BASE_URL, pass: false, journeys: {}, runtime: {} };
  const errorRecovery = {};
  const accessibility = { engine: '@axe-core/playwright@4.10.2', scans: [], blocking: 0 };
  const responsive = { viewports: [], pages: [], horizontal_overflow: 0 };
  const performanceReport = { runs_per_scenario: PERF_RUNS, scenarios: {}, budgets: {}, relative_regression_percent: null };
  let context;
  try {
    context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
    await context.tracing.start({ screenshots: true, snapshots: true, sources: false });
    let page = await context.newPage();
    let runtime = capture(page);
    await login(page, 'demo_role_finance');

    if (process.env.DELIVERY_HARDENING_A11Y_PROBE === '1') {
      await open(page, recordRoute(TARGETS.work_settlement));
      await page.getByRole('button', { name: '新建付款申请' }).click();
      await page.locator('[data-field-name="amount"] input').waitFor({ timeout: 45000 });
      accessibility.scans.push(await axe(page, 'payment-form'));
      const removeProbe = await interceptNextBusiness(page, (route) => route.abort('failed'), TARGETS.payment_request);
      await page.goto(`${BASE_URL}${recordRoute(TARGETS.payment_request)}`, { waitUntil: 'domcontentloaded' });
      await page.getByRole('heading', { name: '网络连接异常' }).waitFor({ timeout: 45000 });
      accessibility.scans.push(await axe(page, 'network-error'));
      await removeProbe();
      accessibility.blocking = accessibility.scans.reduce((sum, row) => sum + row.blocking, 0);
      fs.writeFileSync(path.join(OUT, 'accessibility-probe.json'), `${JSON.stringify(accessibility, null, 2)}\n`);
      console.log(`[verify.frontend.delivery_hardening.a11y_probe] findings=${accessibility.blocking}`);
      return;
    }

    if (!PERF_ONLY) {
    // J09: network, conflict and expired-session recovery use the real current request.
    let remove = await interceptNextBusiness(page, (route) => route.abort('failed'), TARGETS.payment_request);
    await open(page, recordRoute(TARGETS.payment_request));
    await page.getByRole('heading', { name: '网络连接异常' }).waitFor({ timeout: 30000 });
    await remove();
    await page.getByRole('button', { name: '重试' }).click();
    await page.locator('.financial-workspace[data-workspace-kind="payment_request"]').waitFor({ timeout: 45000 });
    errorRecovery.network_retry = 'PASS';

    remove = await interceptNextBusiness(page, (route) => fulfillError(route, 409, 'CONFLICT', 'stale write conflict'), TARGETS.payment_request);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: '数据已发生变化' }).waitFor({ timeout: 30000 });
    await remove();
    await page.getByRole('button', { name: '获取最新数据' }).click();
    await page.locator('.financial-workspace[data-workspace-kind="payment_request"]').waitFor({ timeout: 45000 });
    errorRecovery.conflict_refresh = 'PASS';

    remove = await interceptNextBusiness(page, (route) => fulfillError(route, 401, 'SESSION_EXPIRED', 'expired'), TARGETS.payment_request);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForURL(/\/login\?reason=session_expired/, { timeout: 30000 });
    check(!page.url().includes('redirect=') && new URL(page.url()).pathname === '/login', 'expired session retained sensitive route');
    await remove();
    errorRecovery.session_expired = 'PASS';
    report.journeys.J09 = 'PASS';
    await page.waitForTimeout(300);
    check(!runtime.pageerror.length, `J09 pageerror=${runtime.pageerror.join(' | ')}`);
    check(runtime.console.every((line) => /Failed to load resource/i.test(line)), `J09 unexpected console=${runtime.console.join(' | ')}`);
    check(runtime.http.every((row) => [401, 409].includes(row.status)), `J09 unexpected HTTP=${JSON.stringify(runtime.http)}`);
    errorRecovery.expected_injected_browser_errors = { console: runtime.console.length, http: runtime.http.length };
    await page.close();
    page = await context.newPage();
    runtime = capture(page);

    // J10: narrow-screen keyboard path and native dialog focus containment/restore.
    await page.setViewportSize({ width: 390, height: 844 });
    await login(page, 'demo_role_finance', true);
    await page.getByRole('button', { name: '我的工作' }).focus();
    await page.keyboard.press('Enter');
    await page.locator('.product-work').waitFor({ timeout: 45000 });
    await page.locator('.count-card[data-section-key="todo"]').press('Enter');
    const cardButton = page.locator('.work-section[data-section-key="todo"] .work-card').filter({ hasText: 'FE-JOURNEY-PAYMENT-001' }).getByRole('button', { name: '打开详情' }).first();
    const workUrl = page.url();
    await cardButton.focus(); await cardButton.press('Enter');
    await page.waitForFunction((previous) => window.location.href !== previous, workUrl, { timeout: 45000 });
    check(new URL(page.url()).pathname.startsWith('/r/payment.request/'), `J10 My Work target route invalid: ${page.url()}`);
    await page.getByText('FE-JOURNEY-PAYMENT-001', { exact: false }).first().waitFor({ timeout: 45000 });
    await open(page, recordRoute(TARGETS.journey_request));
    const submit = page.locator('.template-page-header-actions button').filter({ hasText: /^提交$/ }).first();
    await submit.focus(); await submit.press('Enter');
    const dialog = page.getByRole('dialog');
    await dialog.waitFor({ timeout: 15000 });
    check(await dialog.getByRole('button', { name: '确认提交' }).evaluate((node) => node === document.activeElement), 'dialog initial focus missing');
    await page.keyboard.press('Tab'); await page.keyboard.press('Tab');
    check(await dialog.evaluate((node) => node.contains(document.activeElement)), 'dialog focus escaped');
    await page.keyboard.press('Escape');
    check(await submit.evaluate((node) => node === document.activeElement), 'dialog focus did not return');
    await assertNoOverflow(page, 'J10');
    report.journeys.J10 = 'PASS';

    // J11: force system.init response reordering; epoch must retain only final company B.
    await page.setViewportSize({ width: 1440, height: 900 });
    let initSequence = 0;
    const reorder = async (route) => {
      let intent = ''; try { intent = JSON.parse(route.request().postData() || '{}').intent || ''; } catch {}
      if (intent === 'system.init') {
        initSequence += 1;
        await new Promise((resolve) => setTimeout(resolve, initSequence === 1 ? 900 : initSequence === 2 ? 500 : 80));
      }
      await route.continue();
    };
    await page.route('**/api/v1/intent**', reorder);
    const company = page.getByLabel('当前公司');
    await company.selectOption({ label: 'FE Company B' });
    await company.selectOption({ label: 'FE Company A' });
    await company.selectOption({ label: 'FE Company B' });
    await page.waitForTimeout(1800);
    await page.goto(`${BASE_URL}/my-work`, { waitUntil: 'domcontentloaded' });
    await page.locator('.product-work').waitFor({ timeout: 45000 });
    const workText = await page.locator('body').innerText();
    check(workText.includes('FE-C-PR-001') && !workText.includes('FE-JOURNEY-PAYMENT-001'), 'stale company response polluted final B context');
    await page.unroute('**/api/v1/intent**', reorder);
    await logout(page); await login(page, 'demo_role_project_a_member');
    await page.goto(`${BASE_URL}/my-work`); await page.locator('.product-work').waitFor({ timeout: 45000 });
    const memberText = await page.locator('body').innerText();
    check(!/FE-C-PR-001|FE-JOURNEY-PAYMENT|80\.00|100\.00/.test(memberText), 'finance data survived role switch');
    report.journeys.J11 = 'PASS';
    assertRuntimeClean(runtime, 'J10-J11');

    // Representative responsive and accessibility matrix. Existing role permissions are preserved.
    const surfaces = [
      { name: 'login', route: '/login', role: '' }, { name: 'home', route: '/', role: 'demo_role_finance' }, { name: 'my-work', route: '/my-work', role: 'demo_role_finance' },
      { name: 'project-list', route: listRoute(TARGETS.project), role: 'demo_role_pm' }, { name: 'project-detail', route: recordRoute(TARGETS.project), role: 'demo_role_pm' },
      { name: 'contract-list', route: listRoute(TARGETS.contract), role: 'demo_role_finance' }, { name: 'contract-detail', route: recordRoute(TARGETS.contract), role: 'demo_role_finance' },
      { name: 'settlement-list', route: listRoute(TARGETS.settlement), role: 'demo_role_finance' }, { name: 'settlement-detail', route: recordRoute(TARGETS.settlement), role: 'demo_role_finance' },
      { name: 'payment-list', route: listRoute(TARGETS.payment_request), role: 'demo_role_finance' }, { name: 'payment-detail', route: recordRoute(TARGETS.payment_request), role: 'demo_role_finance' },
      { name: 'payment-form', route: recordRoute(TARGETS.work_settlement), role: 'demo_role_finance', mode: 'form' },
      { name: 'execution-detail', route: recordRoute(TARGETS.payment_execution), role: 'demo_role_finance' },
      { name: 'approval-dialog', route: recordRoute(TARGETS.journey_request), role: 'demo_role_finance', mode: 'dialog' },
      { name: 'denied', route: recordRoute(TARGETS.payment_request), role: 'demo_role_project_a_member' },
      { name: 'not-found', route: `/r/payment.request/999999?action_id=${TARGETS.payment_request.action_id}&menu_id=${TARGETS.payment_request.menu_id}`, role: 'demo_role_finance' },
      { name: 'network-error', route: recordRoute(TARGETS.payment_request), role: 'demo_role_finance', mode: 'network' },
      { name: 'legal-empty-relationship', route: recordRoute(TARGETS.payment_request), role: 'demo_role_finance' },
    ];
    for (const viewport of [{ width: 1440, height: 900 }, { width: 1280, height: 800 }, { width: 768, height: 1024 }, { width: 390, height: 844 }]) {
      responsive.viewports.push(viewport);
      await page.setViewportSize(viewport);
      await logout(page).catch(() => {});
      let currentRole = '';
      for (const surface of surfaces) {
        let removeFault = null;
        let faultSnapshot = null;
        if (!surface.role) {
          await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded' });
          currentRole = '';
        } else {
          if (currentRole !== surface.role || page.url().includes('/login')) {
            if (currentRole) await logout(page).catch(() => {});
            await login(page, surface.role);
            currentRole = surface.role;
          }
          if (surface.name === 'denied') {
            faultSnapshot = { console: runtime.console.length, http: runtime.http.length, pageerror: runtime.pageerror.length };
            runtime.expectForbidden = true;
          }
          if (surface.mode === 'network') {
            faultSnapshot = { console: runtime.console.length, http: runtime.http.length, pageerror: runtime.pageerror.length };
            removeFault = await interceptNextBusiness(page, (route) => route.abort('failed'), TARGETS.payment_request);
          }
          await page.goto(`${BASE_URL}${surface.route}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
          if (surface.mode === 'form') {
            await page.locator('.financial-workspace[data-workspace-kind="settlement"]').waitFor({ timeout: 45000 });
            await page.getByRole('button', { name: '新建付款申请' }).click();
            await page.locator('[data-field-name="amount"] input').waitFor({ timeout: 45000 });
          } else if (surface.mode === 'dialog') {
            await page.locator('.financial-workspace[data-workspace-kind="payment_request"]').waitFor({ timeout: 45000 });
            await page.locator('.template-page-header-actions button.sc-btn-primary').filter({ hasText: /^提交$/ }).first().click();
            await page.getByRole('dialog').waitFor({ timeout: 15000 });
          } else if (surface.mode === 'network') {
            await page.getByRole('heading', { name: '网络连接异常' }).waitFor({ timeout: 45000 });
          } else if (surface.name === 'denied') {
            await page.getByRole('heading', { name: '无权访问' }).waitFor({ timeout: 45000 });
          } else {
            await page.waitForTimeout(250);
          }
        }
        await assertNoOverflow(page, `${surface.name}-${viewport.width}`);
        const shot = path.join(SCREENSHOTS, `${surface.name}-${viewport.width}x${viewport.height}.png`);
        await page.screenshot({ path: shot, fullPage: false });
        responsive.pages.push({ name: surface.name, role: surface.role || 'anonymous', viewport, pass: true, screenshot: shot });
        if (viewport.width === 1440) {
          const scan = await axe(page, surface.name);
          accessibility.scans.push(scan); accessibility.blocking += scan.blocking;
        }
        if (surface.mode === 'dialog') await page.keyboard.press('Escape');
        if (surface.name === 'denied' && faultSnapshot) {
          await page.waitForTimeout(250);
          runtime.expectForbidden = false;
          const expectedConsole = runtime.console.slice(faultSnapshot.console);
          const expectedHttp = runtime.http.slice(faultSnapshot.http);
          check(expectedConsole.every((line) => /Failed to load resource/i.test(line)), `denied surface unexpected console=${expectedConsole.join(' | ')}`);
          check(expectedHttp.every((row) => row.status === 403), `denied surface unexpected HTTP=${JSON.stringify(expectedHttp)}`);
          check(runtime.pageerror.length === faultSnapshot.pageerror, 'denied surface caused pageerror');
          runtime.console.length = faultSnapshot.console;
          runtime.http.length = faultSnapshot.http;
        }
        if (removeFault) {
          await removeFault();
          await page.getByRole('button', { name: '重试' }).click();
          await page.locator('.financial-workspace').waitFor({ timeout: 45000 });
          const injectedConsole = runtime.console.slice(faultSnapshot.console);
          check(injectedConsole.every((line) => /Failed to load resource/i.test(line)), `responsive network unexpected console=${injectedConsole.join(' | ')}`);
          check(runtime.pageerror.length === faultSnapshot.pageerror, 'responsive network caused pageerror');
          runtime.console.length = faultSnapshot.console;
          runtime.http.length = faultSnapshot.http;
        }
      }
    }
    check(accessibility.blocking === 0, `accessibility blocking findings=${accessibility.blocking}`);
    }

    // Five-run fixed-runtime measurements: login and true SPA navigation, without fixture mutation.
    const performanceRequests = [];
    page.on('request', (request) => {
      if (!request.url().includes('/api/v1/intent')) return;
      try {
        const payload = JSON.parse(request.postData() || '{}');
        performanceRequests.push(`${payload.intent || ''}:${payload.params?.op || ''}:${payload.params?.model || ''}`);
      } catch {}
    });
    await page.setViewportSize({ width: 1440, height: 900 });
    await logout(page).catch(() => {});
    await login(page, 'demo_role_finance');
    const loginSamples = [];
    for (let i = 0; i < PERF_RUNS; i += 1) {
      await logout(page);
      loginSamples.push(await time(() => login(page, 'demo_role_finance')));
    }
    performanceReport.scenarios.login_to_interactive = stats(loginSamples);
    for (const [name, route, readySelector] of [
      ['my_work', '/my-work', '.product-work'],
      ['payment_detail', recordRoute(TARGETS.payment_request), '.financial-workspace[data-workspace-kind="payment_request"]'],
      ['settlement_detail', recordRoute(TARGETS.settlement), '.financial-workspace[data-workspace-kind="settlement"]'],
      ['execution_detail', recordRoute(TARGETS.payment_execution), '.financial-workspace[data-workspace-kind="payment_execution"]'],
    ]) {
      const samples = [];
      const requestSamples = [];
      for (let i = 0; i < PERF_RUNS; i += 1) {
        if (name === 'my_work') {
          await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });
          await page.waitForTimeout(2000);
        } else {
          await navigateSpa(page, '/my-work', '.product-work');
        }
        const requestOffset = performanceRequests.length;
        samples.push(await time(() => navigateSpa(page, route, readySelector)));
        requestSamples.push(performanceRequests.slice(requestOffset));
      }
      performanceReport.scenarios[name] = { ...stats(samples), request_samples: requestSamples };
    }
    const formSamples = [];
    for (let i = 0; i < PERF_RUNS; i += 1) {
      await navigateSpa(page, recordRoute(TARGETS.work_settlement), '.financial-workspace[data-workspace-kind="settlement"]');
      formSamples.push(await time(async () => {
        await page.locator('.financial-workspace[data-workspace-kind="settlement"]').getByRole('button', { name: '新建付款申请', exact: true }).click();
        await page.waitForURL((url) => /\/payment\.request\/new$/.test(url.pathname), { timeout: 45000 });
        await page.locator('[data-field-name="amount"] input').waitFor({ timeout: 45000 });
      }));
    }
    performanceReport.scenarios.form_open = stats(formSamples);
    if (PERF_BASELINE_CAPTURE) {
      performanceReport.baseline_scope = 'login_and_initialized_navigation';
      fs.writeFileSync(path.join(OUT, 'performance-baseline.json'), `${JSON.stringify(performanceReport, null, 2)}\n`);
      console.log('[verify.frontend.delivery_hardening.performance_baseline] CAPTURED');
      return;
    }
    const switchSamples = [];
    for (let i = 0; i < PERF_RUNS; i += 1) {
      switchSamples.push(await time(() => selectCompany(page, i % 2 ? 'FE Company A' : 'FE Company B')));
    }
    performanceReport.scenarios.company_switch = stats(switchSamples);
    performanceReport.budgets = { login_median_ms: 3000, login_slowest_ms: 5000, initialized_navigation_median_ms: 1200, initialized_navigation_slowest_ms: 2500, company_switch_median_ms: 2000, company_switch_slowest_ms: 4000 };

    const loginBudget = performanceReport.scenarios.login_to_interactive;
    const companyBudget = performanceReport.scenarios.company_switch;
    const absoluteScenarioPass = {
      login_to_interactive: loginBudget.median_ms <= 3000 && loginBudget.slowest_ms <= 5000,
      my_work: performanceReport.scenarios.my_work.median_ms <= 1200 && performanceReport.scenarios.my_work.slowest_ms <= 2500,
      payment_detail: performanceReport.scenarios.payment_detail.median_ms <= 1200 && performanceReport.scenarios.payment_detail.slowest_ms <= 2500,
      settlement_detail: performanceReport.scenarios.settlement_detail.median_ms <= 1200 && performanceReport.scenarios.settlement_detail.slowest_ms <= 2500,
      execution_detail: performanceReport.scenarios.execution_detail.median_ms <= 1200 && performanceReport.scenarios.execution_detail.slowest_ms <= 2500,
      form_open: performanceReport.scenarios.form_open.median_ms <= 1200 && performanceReport.scenarios.form_open.slowest_ms <= 2500,
      company_switch: companyBudget.median_ms <= 2000 && companyBudget.slowest_ms <= 4000,
    };
    performanceReport.absolute_scenario_pass = absoluteScenarioPass;
    performanceReport.absolute_budget_pass = Object.values(absoluteScenarioPass).every(Boolean);
    if (PERF_BASELINE_PATH) {
      const baseline = JSON.parse(fs.readFileSync(PERF_BASELINE_PATH, 'utf8'));
      const metricRegressions = Object.fromEntries(Object.entries(performanceReport.scenarios).map(([key, current]) => {
        const previous = baseline.scenarios?.[key];
        return [key, Object.fromEntries(['median_ms', 'slowest_ms'].map((metric) => [
          metric,
          previous?.[metric] > 0 ? ((current[metric] - previous[metric]) / previous[metric]) * 100 : null,
        ]))];
      }));
      const regressions = Object.values(metricRegressions).flatMap((row) => Object.values(row)).filter((value) => typeof value === 'number');
      performanceReport.metric_regression_percent = metricRegressions;
      performanceReport.relative_regression_percent = Math.max(...regressions, 0);
      performanceReport.relative_baseline_path = PERF_BASELINE_PATH;
      const absoluteMetricBudgets = {
        login_to_interactive: { median_ms: 3000, slowest_ms: 5000 },
        my_work: { median_ms: 1200, slowest_ms: 2500 },
        payment_detail: { median_ms: 1200, slowest_ms: 2500 },
        settlement_detail: { median_ms: 1200, slowest_ms: 2500 },
        execution_detail: { median_ms: 1200, slowest_ms: 2500 },
        form_open: { median_ms: 1200, slowest_ms: 2500 },
        company_switch: { median_ms: 2000, slowest_ms: 4000 },
      };
      performanceReport.relative_budget_pass = Object.entries(absoluteMetricBudgets).every(([key, budgets]) => (
        Object.entries(budgets).every(([metric, budget]) => (
          performanceReport.scenarios[key][metric] <= budget
          || (typeof metricRegressions[key]?.[metric] === 'number' && metricRegressions[key][metric] <= 10)
        ))
      ));
    } else {
      performanceReport.relative_budget_pass = false;
    }
    check(performanceReport.absolute_budget_pass || performanceReport.relative_budget_pass, `performance budget exceeded: ${JSON.stringify(performanceReport.scenarios)}`);
    if (PERF_ONLY) {
      fs.writeFileSync(path.join(OUT, 'performance-probe.json'), `${JSON.stringify(performanceReport, null, 2)}\n`);
      console.log('[verify.frontend.delivery_hardening.performance_probe] PASS');
      return;
    }

    assertRuntimeClean(runtime, 'final delivery hardening runtime');
    errorRecovery.expected_denied_browser_errors = {
      console: runtime.expectedConsole.length,
      http: runtime.expectedHttp.length,
    };
    report.pass = true;
    report.evidence = responsive.pages.map((row) => ({ role: row.role, viewport: row.viewport, journey: 'responsive', surface: row.name, pass: row.pass, screenshot: row.screenshot }));
    report.runtime = {
      console: runtime.console,
      pageerror: runtime.pageerror,
      unhandled: runtime.unhandled,
      http: runtime.http,
    };
    await context.tracing.stop({ path: path.join(TRACES, 'j09-j11-responsive-performance.zip') });
    fs.writeFileSync(path.join(OUT, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
    fs.writeFileSync(path.join(OUT, 'performance.json'), `${JSON.stringify(performanceReport, null, 2)}\n`);
    fs.writeFileSync(path.join(OUT, 'accessibility.json'), `${JSON.stringify(accessibility, null, 2)}\n`);
    fs.writeFileSync(path.join(OUT, 'responsive.json'), `${JSON.stringify(responsive, null, 2)}\n`);
    fs.writeFileSync(path.join(OUT, 'error-recovery.json'), `${JSON.stringify(errorRecovery, null, 2)}\n`);
    console.log(`[verify.frontend.delivery_hardening.browser] PASS J09-J11 responsive=${responsive.pages.length} accessibility_blocking=0`);
  } catch (error) {
    if (context) {
      const pages = context.pages();
      if (pages[0]) await pages[0].screenshot({ path: path.join(SCREENSHOTS, 'failure.png'), fullPage: true }).catch(() => {});
    }
    fs.writeFileSync(path.join(OUT, 'accessibility.json'), `${JSON.stringify(accessibility, null, 2)}\n`);
    fs.writeFileSync(path.join(OUT, 'responsive.json'), `${JSON.stringify(responsive, null, 2)}\n`);
    fs.writeFileSync(path.join(OUT, 'error-recovery.json'), `${JSON.stringify(errorRecovery, null, 2)}\n`);
    fs.writeFileSync(path.join(OUT, 'failure.json'), `${JSON.stringify({ report, accessibility, error: error.stack || error.message }, null, 2)}\n`);
    await context?.tracing.stop({ path: path.join(TRACES, 'failure.zip') }).catch(() => {});
    throw error;
  } finally {
    await context?.close(); await browser.close();
  }
}

main().catch((error) => { console.error(`[verify.frontend.delivery_hardening.browser] FAIL ${error.stack || error.message}`); process.exitCode = 1; });
