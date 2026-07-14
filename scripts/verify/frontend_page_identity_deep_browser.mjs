#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { launchChromium } from './playwright_runtime.mjs';

const BASE_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const DB_NAME = process.env.DB_NAME || 'sc_frontend_acceptance';
const PASSWORD = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const OUTPUT_DIR = process.env.ARTIFACTS_DIR || 'artifacts/frontend-page-identity-deep';
const TARGETS = JSON.parse(process.env.FRONTEND_PAGE_IDENTITY_DEEP_TARGETS_JSON || '{}');
const TECHNICAL = /(?:[a-z_][a-z0-9_]*\.)+[a-z_][a-z0-9_]*|\s#\d+|undefined|null|\b(?:action|menu|record)_?id\b/i;

fs.mkdirSync(OUTPUT_DIR, { recursive: true });

function requireCheck(condition, message) {
  if (!condition) throw new Error(message);
}

function listRoute(target) {
  return `/a/${target.action_id}?menu_id=${target.menu_id}`;
}

function recordRoute(target, mode = 'detail', recordId = target.record_id) {
  const prefix = mode === 'edit' ? '/f' : '/r';
  return `${prefix}/${encodeURIComponent(target.model)}/${recordId}?action_id=${target.action_id}&menu_id=${target.menu_id}`;
}

function attachCapture(page) {
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
    try { body = (await response.text()).slice(0, 20000); } catch {}
    state.responses.push({ intent, status: response.status(), body });
  });
  return {
    reset() {
      state.consoleErrors = [];
      state.pageErrors = [];
      state.responses = [];
    },
    snapshot() {
      return {
        console_errors: [...state.consoleErrors],
        page_errors: [...state.pageErrors],
        responses: state.responses.map(({ intent, status }) => ({ intent, status })),
        rawResponses: [...state.responses],
      };
    },
  };
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
}

async function logout(page) {
  await page.getByRole('button', { name: '退出登录' }).click();
  await page.waitForURL((url) => url.pathname.includes('/login'), { timeout: 30000 });
}

async function waitForIdentity(page, expectedTitle) {
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
  await page.waitForFunction((expected) => {
    const shell = document.querySelector('.layout-shell');
    return shell?.getAttribute('data-page-identity-title') === expected;
  }, expectedTitle, { timeout: 45000 });
}

async function identitySnapshot(page) {
  const shell = page.locator('.layout-shell');
  const heading = String(await page.locator('h1.headline').first().innerText().catch(() => '')).trim();
  return {
    heading,
    title: String(await shell.getAttribute('data-page-identity-title') || '').trim(),
    document_title: await page.title(),
    identity_source: String(await shell.getAttribute('data-page-identity-source') || '').trim(),
    breadcrumbs: (await page.locator('.breadcrumb .crumb').allTextContents()).map((value) => value.trim()).filter(Boolean),
  };
}

async function inspectScenario(page, capture, input) {
  process.stderr.write(`[page-identity-deep] start ${input.id} ${input.route}\n`);
  capture.reset();
  await page.goto(`${BASE_URL}${input.route}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  try {
    await waitForIdentity(page, input.expectedTitle);
  } catch (error) {
    const diagnostic = {
      id: input.id,
      route: input.route,
      final_url: page.url(),
      body: (await page.locator('body').innerText().catch(() => '')).slice(0, 3000),
      wire: capture.snapshot(),
    };
    await page.screenshot({ path: path.join(OUTPUT_DIR, `${input.id}-failure.png`), fullPage: true }).catch(() => {});
    fs.writeFileSync(path.join(OUTPUT_DIR, `${input.id}-failure.json`), `${JSON.stringify(diagnostic, null, 2)}\n`);
    throw new Error(`${input.id}: identity did not settle: ${error.message}; final=${diagnostic.final_url}; body=${diagnostic.body.slice(0, 500)}`);
  }
  const beforeRefresh = await identitySnapshot(page);
  requireCheck(beforeRefresh.heading === input.expectedTitle, `${input.id}: heading mismatch ${beforeRefresh.heading}`);
  requireCheck(beforeRefresh.document_title === `${input.expectedTitle} - 智能施工企业管理平台`, `${input.id}: document title mismatch`);
  requireCheck(beforeRefresh.identity_source === input.expectedSource, `${input.id}: source mismatch ${beforeRefresh.identity_source}`);
  requireCheck(beforeRefresh.breadcrumbs.length > 0, `${input.id}: breadcrumbs missing`);
  requireCheck(beforeRefresh.breadcrumbs.at(-1) === input.expectedTitle, `${input.id}: current breadcrumb mismatch`);
  requireCheck(!TECHNICAL.test(`${beforeRefresh.title} ${beforeRefresh.document_title} ${beforeRefresh.breadcrumbs.join(' ')}`), `${input.id}: technical identity fallback`);
  await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForIdentity(page, input.expectedTitle);
  const afterRefresh = await identitySnapshot(page);
  requireCheck(afterRefresh.document_title === beforeRefresh.document_title, `${input.id}: refresh title drift`);
  requireCheck(JSON.stringify(afterRefresh.breadcrumbs) === JSON.stringify(beforeRefresh.breadcrumbs), `${input.id}: refresh breadcrumb drift`);
  const wire = capture.snapshot();
  const allowedHttpStatuses = new Set(input.allowedHttpStatuses || []);
  const consoleErrors = wire.console_errors.filter((line) => !(allowedHttpStatuses.has(404) && /status of 404/i.test(line)));
  const unexpectedHttp = wire.responses.filter((row) => row.status >= 400 && !allowedHttpStatuses.has(row.status));
  requireCheck(consoleErrors.length === 0, `${input.id}: console errors ${consoleErrors.join(' | ')}`);
  requireCheck(wire.page_errors.length === 0, `${input.id}: page errors ${wire.page_errors.join(' | ')}`);
  requireCheck(unexpectedHttp.length === 0, `${input.id}: unexpected HTTP ${JSON.stringify(unexpectedHttp)}`);
  process.stderr.write(`[page-identity-deep] pass ${input.id}\n`);
  return { ...input, status: 'PASS', before_refresh: beforeRefresh, after_refresh: afterRefresh, network: wire.responses };
}

async function selectCompany(page, companyName) {
  const selector = page.locator('label.business-scope-field select').filter({ has: page.locator(`option:has-text("${companyName}")`) }).first();
  await selector.waitFor({ timeout: 30000 });
  await selector.selectOption({ label: companyName });
  await page.waitForTimeout(500);
  await page.waitForFunction((name) => [...document.querySelectorAll('label.business-scope-field select')]
    .some((node) => node.selectedOptions?.[0]?.textContent?.trim() === name), companyName, { timeout: 30000 });
}

async function waitForCompanyRecord(page, capture, companyName, recordName) {
  try {
    await page.waitForFunction((name) => (document.body.innerText || '').includes(name), recordName, { timeout: 45000 });
  } catch (error) {
    const diagnostic = {
      company: companyName,
      record: recordName,
      url: page.url(),
      selected_companies: await page.locator('label.business-scope-field select').evaluateAll((nodes) => nodes.map((node) => node.selectedOptions?.[0]?.textContent?.trim() || '')),
      body: (await page.locator('body').innerText().catch(() => '')).slice(0, 5000),
      wire: capture.snapshot(),
    };
    await page.screenshot({ path: path.join(OUTPUT_DIR, '15-company-switch-failure.png'), fullPage: true }).catch(() => {});
    fs.writeFileSync(path.join(OUTPUT_DIR, '15-company-switch-failure.json'), `${JSON.stringify(diagnostic, null, 2)}\n`);
    throw error;
  }
}

async function main() {
  for (const key of ['project', 'contract', 'settlement', 'payment_request', 'payment_execution']) {
    requireCheck(TARGETS[key]?.action_id > 0 && TARGETS[key]?.menu_id > 0 && TARGETS[key]?.record_id > 0, `missing deep target ${key}`);
  }
  const browser = await launchChromium({ headless: true });
  const report = { pass: false, scenarios: [], console_page_errors: 0, unexpected_http_errors: 0 };
  try {
    let page = await browser.newPage({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
    let capture = attachCapture(page);
    await login(page, 'demo_role_finance');

    for (const [id, targetKey, type] of [
      ['05-settlement-list', 'settlement', 'list'],
      ['06-settlement-detail', 'settlement', 'detail'],
      ['07-payment-request-list', 'payment_request', 'list'],
      ['08-payment-request-detail', 'payment_request', 'detail'],
      ['09-payment-execution-list', 'payment_execution', 'list'],
      ['10-payment-execution-detail', 'payment_execution', 'detail'],
    ]) {
      const target = TARGETS[targetKey];
      const isList = type === 'list';
      report.scenarios.push(await inspectScenario(page, capture, {
        id,
        role: 'finance',
        route: isList ? listRoute(target) : recordRoute(target),
        expectedTitle: isList ? target.action_name : target.display_name,
        expectedSource: isList ? 'action' : 'record',
        menu_xmlid: target.menu_xmlid,
        action_xmlid: target.action_xmlid,
      }));
    }

    const payment = TARGETS.payment_request;
    report.scenarios.push(await inspectScenario(page, capture, {
      id: '11-create-form', role: 'finance', route: recordRoute(payment, 'detail', 'new'),
      expectedTitle: `新建${payment.action_name}`, expectedSource: 'menu', menu_xmlid: payment.menu_xmlid, action_xmlid: payment.action_xmlid,
    }));
    report.scenarios.push(await inspectScenario(page, capture, {
      id: '12-edit-form', role: 'finance', route: recordRoute(payment, 'edit'),
      expectedTitle: `编辑 ${payment.display_name}`, expectedSource: 'record', menu_xmlid: payment.menu_xmlid, action_xmlid: payment.action_xmlid,
    }));
    report.scenarios.push(await inspectScenario(page, capture, {
      id: '14-not-found', role: 'finance', route: recordRoute(payment, 'detail', 999999999),
      expectedTitle: '记录不存在', expectedSource: 'product-fallback', allowedHttpStatuses: [404], menu_xmlid: payment.menu_xmlid, action_xmlid: payment.action_xmlid,
    }));

    process.stderr.write('[page-identity-deep] start 15-company-a-b-a\n');
    await page.close();
    page = await browser.newPage({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
    capture = attachCapture(page);
    await login(page, 'demo_role_finance');
    capture.reset();
    await page.goto(`${BASE_URL}/m/${payment.menu_id}?action_id=${payment.action_id}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await waitForIdentity(page, payment.action_name);
    await page.locator('section.page[data-product-page-mode="list"]').first().waitFor({ timeout: 45000 });
    await selectCompany(page, 'FE Company A');
    await waitForCompanyRecord(page, capture, 'FE Company A', 'FE-A-PR-001');
    const companyA = await identitySnapshot(page);
    await selectCompany(page, 'FE Company B');
    await waitForCompanyRecord(page, capture, 'FE Company B', 'FE-C-PR-001');
    const companyBText = await page.locator('body').innerText();
    const companyB = await identitySnapshot(page);
    requireCheck(!companyBText.includes('FE-A-PR-001'), '15-company-switch: company A record remained in company B');
    await selectCompany(page, 'FE Company A');
    await waitForCompanyRecord(page, capture, 'FE Company A', 'FE-A-PR-001');
    const companyAReturn = await identitySnapshot(page);
    requireCheck(companyA.title === companyB.title && companyB.title === companyAReturn.title, '15-company-switch: title context drift');
    requireCheck(!TECHNICAL.test(`${companyAReturn.title} ${companyAReturn.breadcrumbs.join(' ')}`), '15-company-switch: technical fallback');
    let wire = capture.snapshot();
    requireCheck(wire.console_errors.length === 0 && wire.page_errors.length === 0 && !wire.responses.some((row) => row.status >= 400), '15-company-switch: browser/network errors');
    report.scenarios.push({ id: '15-company-a-b-a', role: 'finance', status: 'PASS', company_a: companyA, company_b: companyB, company_a_return: companyAReturn });
    process.stderr.write('[page-identity-deep] pass 15-company-a-b-a\n');

    process.stderr.write('[page-identity-deep] start 16-logout-role-switch\n');
    await logout(page);
    await login(page, 'demo_role_project_a_member');
    const memberLanding = await identitySnapshot(page);
    requireCheck(!/付款|结算|实付/.test(`${memberLanding.title} ${memberLanding.breadcrumbs.join(' ')}`), '16-role-switch: finance identity leaked after logout');
    report.scenarios.push({ id: '16-logout-role-switch', role: 'finance->project_member', status: 'PASS', identity: memberLanding });
    process.stderr.write('[page-identity-deep] pass 16-logout-role-switch\n');

    await logout(page);
    await login(page, 'demo_role_pm');

    for (const [id, targetKey, type] of [
      ['01-project-list', 'project', 'list'],
      ['02-project-detail', 'project', 'detail'],
      ['03-contract-list', 'contract', 'list'],
      ['04-contract-detail', 'contract', 'detail'],
    ]) {
      const target = TARGETS[targetKey];
      const isList = type === 'list';
      report.scenarios.push(await inspectScenario(page, capture, {
        id,
        role: 'pm',
        route: isList ? listRoute(target) : recordRoute(target),
        expectedTitle: isList ? target.action_name : target.display_name,
        expectedSource: isList ? 'action' : 'record',
        menu_xmlid: target.menu_xmlid,
        action_xmlid: target.action_xmlid,
      }));
    }

    process.stderr.write('[page-identity-deep] start 13-permission-denied\n');
    await logout(page);
    await login(page, 'demo_role_project_a_member');
    capture.reset();
    await page.goto(`${BASE_URL}${listRoute(payment)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await waitForIdentity(page, '无权访问');
    const denied = await identitySnapshot(page);
    const deniedBody = await page.locator('body').innerText();
    wire = capture.snapshot();
    requireCheck(denied.identity_source === 'product-fallback', '13-denied: source mismatch');
    requireCheck(!deniedBody.includes(payment.display_name), '13-denied: record name leaked');
    requireCheck(!wire.rawResponses.some((row) => row.intent !== 'system.init' && row.body.includes(payment.display_name)), '13-denied: response leaked record name');
    requireCheck(wire.console_errors.length === 0 && wire.page_errors.length === 0, '13-denied: browser errors');
    report.scenarios.push({ id: '13-permission-denied', role: 'project_member', status: 'PASS', route: listRoute(payment), identity: denied, network: wire.responses });
    process.stderr.write('[page-identity-deep] pass 13-permission-denied\n');

    const expectedIds = new Set([
      '01-project-list', '02-project-detail', '03-contract-list', '04-contract-detail',
      '05-settlement-list', '06-settlement-detail', '07-payment-request-list', '08-payment-request-detail',
      '09-payment-execution-list', '10-payment-execution-detail', '11-create-form', '12-edit-form',
      '13-permission-denied', '14-not-found', '15-company-a-b-a', '16-logout-role-switch',
    ]);
    requireCheck(report.scenarios.length === 16 && report.scenarios.every((row) => expectedIds.has(row.id) && row.status === 'PASS'), 'deep scenario matrix incomplete');
    report.pass = true;
    await page.close();
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
  }
  console.log('[verify.frontend.page_identity.deep] PASS scenarios=16');
}

main().catch((error) => {
  console.error(`[verify.frontend.page_identity.deep] FAIL ${error.stack || error.message}`);
  process.exitCode = 2;
});
