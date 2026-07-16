#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { launchChromium } from './playwright_runtime.mjs';

const BASE_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const DB_NAME = process.env.DB_NAME || 'sc_frontend_acceptance';
const PASSWORD = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const OUTPUT_DIR = process.env.ARTIFACTS_DIR || 'artifacts/frontend-financial-workspace';
const TARGETS = JSON.parse(process.env.FRONTEND_FINANCIAL_WORKSPACE_TARGETS_JSON || '{}');
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

function check(condition, message) {
  if (!condition) throw new Error(message);
}

function route(target) {
  return `/r/${encodeURIComponent(target.model)}/${target.record_id}?action_id=${target.action_id}&menu_id=${target.menu_id}`;
}

function captureRuntime(page) {
  const state = { consoleErrors: [], pageErrors: [], responses: [] };
  page.on('console', (message) => {
    if (message.type() === 'error' && !/favicon|ResizeObserver/i.test(message.text())) state.consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => state.pageErrors.push(error.message));
  page.on('response', async (response) => {
    if (!response.url().includes('/api/v1/intent')) return;
    let intent = '';
    let body = '';
    try { intent = JSON.parse(response.request().postData() || '{}')?.intent || ''; } catch {}
    try { body = (await response.text()).slice(0, 30000); } catch {}
    state.responses.push({ intent, status: response.status(), body });
  });
  return state;
}

function resetRuntime(runtime) {
  runtime.consoleErrors.length = 0;
  runtime.pageErrors.length = 0;
  runtime.responses.length = 0;
}

async function login(page, loginName) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(loginName);
  await inputs.nth(1).fill(PASSWORD);
  if (await inputs.nth(2).isEnabled()) await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
  await page.waitForFunction(() => !(document.body.innerText || '').includes('正在初始化角色首页'), null, { timeout: 45000 });
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

async function selectCompany(page, companyName) {
  const selector = page.locator('label.business-scope-field select').filter({
    has: page.locator(`option:has-text("${companyName}")`),
  }).first();
  await selector.waitFor({ timeout: 30000 });
  const current = await selector.locator('option:checked').innerText();
  const initResponse = current.trim() === companyName
    ? null
    : page.waitForResponse((response) => {
        if (!response.url().includes('/api/v1/intent')) return false;
        try { return JSON.parse(response.request().postData() || '{}')?.intent === 'system.init'; } catch { return false; }
      }, { timeout: 45000 });
  await selector.selectOption({ label: companyName });
  if (initResponse) await initResponse;
  await page.waitForFunction((name) => {
    const select = [...document.querySelectorAll('label.business-scope-field select')]
      .find((node) => [...node.options].some((option) => option.textContent?.trim() === name));
    return select?.selectedOptions?.[0]?.textContent?.trim() === name;
  }, companyName, { timeout: 30000 });
  await page.waitForTimeout(300);
}

async function openWorkspace(page, target, kind) {
  await page.goto(`${BASE_URL}${route(target)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  const workspace = page.locator(`.financial-workspace[data-workspace-kind="${kind}"]`);
  try {
    await workspace.waitFor({ timeout: 45000 });
  } catch (error) {
    throw new Error(`${kind} workspace unavailable; url=${page.url()} body=${(await page.locator('body').innerText()).slice(0, 1800)} cause=${error.message}`);
  }
  return workspace;
}

async function relationship(page, key) {
  const section = page.locator(`[data-relation-key="${key}"]`);
  await section.waitFor({ timeout: 30000 });
  return section;
}

async function follow(page, key, label, targetKind) {
  const section = await relationship(page, key);
  await section.getByRole('button', { name: new RegExp(label) }).click();
  const workspace = page.locator(`.financial-workspace[data-workspace-kind="${targetKind}"]`);
  await workspace.waitFor({ timeout: 45000 });
  return workspace;
}

async function assertIdentity(page, expectedFragment) {
  const heading = String(await page.locator('h1.headline').first().innerText()).trim();
  const title = await page.title();
  const crumbs = (await page.locator('.breadcrumb .crumb').allTextContents()).join(' / ');
  check(heading.includes(expectedFragment), `heading lacks ${expectedFragment}: ${heading}`);
  check(title.includes(expectedFragment) && title.endsWith(' - 智能施工企业管理平台'), `document title mismatch: ${title}`);
  check(crumbs && !/(?:[a-z_]\w*\.)+[a-z_]\w*|#\d+/.test(crumbs), `technical breadcrumb: ${crumbs}`);
  return { heading, title, crumbs };
}

async function assertNoHorizontalOverflow(page, id) {
  const dimensions = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth }));
  check(dimensions.scroll <= dimensions.client + 1, `${id}: horizontal overflow ${dimensions.scroll}/${dimensions.client}`);
}

function assertClean(runtime, id, allowedStatuses = []) {
  const unexpected = runtime.responses.filter((item) => item.status >= 400 && !allowedStatuses.includes(item.status));
  check(runtime.consoleErrors.length === 0, `${id}: console errors ${runtime.consoleErrors.join(' | ')}`);
  check(runtime.pageErrors.length === 0, `${id}: page errors ${runtime.pageErrors.join(' | ')}`);
  check(unexpected.length === 0, `${id}: unexpected HTTP ${JSON.stringify(unexpected.map(({ intent, status }) => ({ intent, status })))}`);
}

async function main() {
  for (const key of ['project', 'contract', 'settlement', 'payment_request', 'payment_execution', 'journey_settlement', 'journey_request']) {
    check(TARGETS[key]?.record_id > 0 && TARGETS[key]?.action_id > 0 && TARGETS[key]?.menu_id > 0, `missing target ${key}`);
  }
  const browser = await launchChromium({ headless: true });
  const report = { pass: false, j04: {}, j05: {}, j06: {}, responsive: [], isolation: {} };
  try {
    // J04 uses PM for the project entry because the frozen finance record rule does not grant Project A read access.
    let page = await browser.newPage({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
    let runtime = captureRuntime(page);
    await login(page, 'demo_role_pm');
    resetRuntime(runtime);
    let workspace = await openWorkspace(page, TARGETS.project, 'project');
    check((await workspace.innerText()).includes('FE Company A'), 'J04 project facts missing');
    await assertIdentity(page, 'FE Project A');
    await follow(page, 'contracts', 'CONOUT2600001', 'contract');
    check((await page.locator('[data-fact-key="amount_total"]').innerText()).includes('1,130.00'), 'J04 contract amount mismatch');
    await follow(page, 'settlements', 'FE-A-SET-001', 'settlement');
    check((await page.locator('[data-fact-key="amount_total"]').innerText()).includes('1,000.00'), 'J04 settlement amount mismatch');
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.locator('.financial-workspace[data-workspace-kind="settlement"]').waitFor({ timeout: 45000 });
    await follow(page, 'contract', 'CONOUT2600001', 'contract');
    check(page.url().includes('/construction.contract/'), 'J04 reverse link did not return to contract');
    assertClean(runtime, 'J04');
    report.j04 = { status: 'PASS', role: 'pm', authority_note: 'finance Project A read remains denied by the frozen record rule' };
    await logout(page);

    // J05 runs entirely as finance over its existing contract/settlement/payment authority.
    await login(page, 'demo_role_finance');
    runtime = captureRuntime(page);
    resetRuntime(runtime);
    await openWorkspace(page, TARGETS.settlement, 'settlement');
    check((await page.locator('[data-fact-key="settlement_reserved"]').innerText()).includes('1,000.00'), 'J05 reserved amount mismatch');
    check((await page.locator('[data-fact-key="settlement_actual_paid"]').innerText()).includes('0.00'), 'J05 actual paid must remain distinct from reservation');
    await follow(page, 'payment_requests', 'FE-A-PR-001', 'payment_request');
    check((await page.locator('[data-fact-key="request_reserved"]').innerText()).includes('1,000.00'), 'J05 request reservation mismatch');
    check((await page.locator('[data-fact-key="paid_amount_total"]').innerText()).includes('0.00'), 'J05 request ledger amount mismatch');
    const ledger = await relationship(page, 'ledgers');
    check((await ledger.innerText()).includes('暂无实付 / 台账结果'), 'J05 missing ledger empty state');
    await follow(page, 'executions', 'FE-A-PE-001', 'payment_execution');
    check((await page.locator('[data-fact-key="planned_amount"]').innerText()).includes('1,000.00'), 'J05 execution amount mismatch');
    check((await page.locator('[data-fact-key="paid_amount"]').innerText()).includes('1,000.00'), 'J05 execution result mismatch');
    await follow(page, 'payment_request', 'FE-A-PR-001', 'payment_request');
    assertClean(runtime, 'J05');
    report.j05 = { status: 'PASS', ledger_result: 'explicit-empty', reservation_and_actual_distinct: true };

    // J06: authoritative draft -> submit intent with confirmation and full reload.
    runtime = captureRuntime(page);
    workspace = await openWorkspace(page, TARGETS.journey_request, 'payment_request');
    const initialState = workspace.locator('.financial-workspace__status[data-state="draft"]');
    await initialState.waitFor({ timeout: 45000 });
    check((await initialState.innerText()).includes('草稿'), 'J06 journey initial state is not draft');
    const submit = page.locator('.template-page-header-actions button').filter({ hasText: /^提交$/ }).first();
    await page.waitForFunction(() => [...document.querySelectorAll('.template-page-header-actions button')]
      .some((node) => node.textContent?.trim() === '提交' && !node.disabled), null, { timeout: 45000 });
    await submit.focus();
    check(await submit.evaluate((node) => node.tabIndex >= 0 && !node.disabled), 'J06 submit button is not keyboard focusable');
    check(await submit.isEnabled(), 'J06 authoritative submit action is disabled');
    await submit.click();
    const dialog = page.getByRole('dialog');
    await dialog.waitFor({ timeout: 15000 });
    const confirmSubmit = dialog.getByRole('button', { name: /^确认提交$/ });
    check(await confirmSubmit.evaluate((node) => node === document.activeElement), 'J06 dialog focus did not enter confirm button');
    await confirmSubmit.press('Enter');
    try {
      await page.locator('.financial-workspace__status[data-state="submit"]').waitFor({ timeout: 45000 });
    } catch (error) {
      const actionWire = runtime.responses.filter((item) => item.intent === 'payment.request.execute').at(-1);
      throw new Error(`J06 state did not refresh; wire=${JSON.stringify(actionWire)} body=${(await page.locator('body').innerText()).slice(0, 2500)} cause=${error.message}`);
    }
    check(await page.locator('.template-page-header-actions button').filter({ hasText: /^提交$/ }).count() === 0, 'J06 submit action remained after authoritative reload');
    check((await page.locator('[role="status"]').allTextContents()).some((text) => /成功|完成|提交/.test(text)), 'J06 success feedback missing');
    await follow(page, 'settlement', 'FE-JOURNEY-SETTLEMENT-001', 'settlement');
    check((await page.locator('[data-fact-key="settlement_reserved"]').innerText()).includes('100.00'), 'J06 upstream reserved summary did not refresh');
    check((await page.locator('[data-fact-key="settlement_remaining"]').innerText()).includes('0.00'), 'J06 upstream remaining summary did not refresh');
    assertClean(runtime, 'J06');
    report.j06 = { status: 'PASS', transition: 'draft->submit', repeat_button_removed: true, upstream_reloaded: true };

    // Company boundary: switching scope clears the open detail, then only the
    // target company's authoritative relationship contract can be opened.
    await openWorkspace(page, TARGETS.payment_request, 'payment_request');
    await selectCompany(page, 'FE Company B');
    await page.waitForURL((url) => url.pathname === '/s/projects.list', { timeout: 45000 });
    try {
      await page.waitForFunction(() => !(document.body.innerText || '').includes('FE-A-PR-001'), null, { timeout: 45000 });
    } catch (error) {
      throw new Error(`company B scope retained A detail; url=${page.url()} console=${JSON.stringify(runtime.consoleErrors)} body=${(await page.locator('body').innerText()).slice(0, 1800)} cause=${error.message}`);
    }
    await openWorkspace(page, TARGETS.payment_request_company_b, 'payment_request');
    await assertIdentity(page, 'FE-C-PR-001');
    check(!(await page.locator('body').innerText()).includes('FE-A-PR-001'), 'company B workspace leaked company A request');
    await selectCompany(page, 'FE Company A');
    await page.waitForURL((url) => url.pathname === '/s/projects.list', { timeout: 45000 });
    await page.waitForFunction(() => !(document.body.innerText || '').includes('FE-C-PR-001'), null, { timeout: 45000 });
    await openWorkspace(page, TARGETS.payment_request, 'payment_request');
    await assertIdentity(page, 'FE-A-PR-001');
    report.isolation.company_a_b_a = 'PASS';

    for (const viewport of [{ width: 1440, height: 900 }, { width: 1280, height: 800 }, { width: 390, height: 844 }]) {
      await page.setViewportSize(viewport);
      resetRuntime(runtime);
      try {
        await openWorkspace(page, TARGETS.settlement, 'settlement');
      } catch (error) {
        throw new Error(`responsive ${viewport.width} settlement unavailable; url=${page.url()} responses=${JSON.stringify(runtime.responses.slice(-4))} body=${(await page.locator('body').innerText()).slice(0, 1800)} cause=${error.message}`);
      }
      await assertNoHorizontalOverflow(page, `${viewport.width}x${viewport.height}`);
      const screenshot = path.join(OUTPUT_DIR, `settlement-${viewport.width}x${viewport.height}.png`);
      await page.screenshot({ path: screenshot, fullPage: true });
      assertClean(runtime, `responsive-${viewport.width}`);
      report.responsive.push({ viewport, status: 'PASS', screenshot });
    }

    await logout(page);
    await login(page, 'demo_role_project_a_member');
    await page.goto(`${BASE_URL}${route(TARGETS.payment_request)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.getByRole('heading', { name: '无权访问', exact: true }).waitFor({ timeout: 45000 });
    const deniedText = await page.locator('body').innerText();
    check(!deniedText.includes('FE-A-PR-001') && !deniedText.includes('1,000.00'), 'project member denial leaked financial facts');
    report.isolation.project_member_denied_without_leak = 'PASS';
    await logout(page);
    await page.close();
    report.pass = true;
    fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
    console.log('[verify.frontend.financial_workspace.browser] PASS');
  } catch (error) {
    fs.writeFileSync(path.join(OUTPUT_DIR, 'failure.json'), `${JSON.stringify({ report, error: error.stack || error.message }, null, 2)}\n`);
    throw error;
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(`[verify.frontend.financial_workspace.browser] FAIL ${error.stack || error.message}`);
  process.exitCode = 1;
});
