#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { launchChromium } from './playwright_runtime.mjs';

const BASE_URL = process.env.FRONTEND_URL || process.env.BASE_URL || 'http://127.0.0.1:18081';
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const PASSWORD = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const OUTPUT_DIR = process.env.ARTIFACTS_DIR || 'artifacts/playwright/frontend-productization-fixture';
const PAYMENT_ACTION_ID = Number(process.env.FRONTEND_FIXTURE_PAYMENT_ACTION_ID || 0);
const PAYMENT_MENU_ID = Number(process.env.FRONTEND_FIXTURE_PAYMENT_MENU_ID || 0);
const PAYMENT_RECORD_A_ID = Number(process.env.FRONTEND_FIXTURE_PAYMENT_RECORD_A_ID || 0);
const PAYMENT_RECORD_C_ID = Number(process.env.FRONTEND_FIXTURE_PAYMENT_RECORD_C_ID || 0);

fs.mkdirSync(OUTPUT_DIR, { recursive: true });
const stage = (name) => { process.stderr.write(`[browser-stage] ${new Date().toISOString()} ${name}\n`); };

function requireCheck(condition, message) {
  if (!condition) throw new Error(message);
}

async function login(page, loginName) {
  const sequence = [];
  page.on('request', (request) => {
    if (!request.url().includes('/api/v1/intent')) return;
    let payload = request.postData() || '';
    payload = payload.replace(/("password"\s*:\s*")[^"]*/g, '$1<redacted>');
    const headers = request.headers();
    sequence.push({ n: sequence.length + 1, phase: 'request', intent: (payload.match(/"intent"\s*:\s*"([^"]+)/) || [,'?'])[1], payload, has_authorization: Boolean(headers.authorization), has_cookie: Boolean(headers.cookie) });
  });
  page.on('response', async (response) => {
    if (!response.url().includes('/api/v1/intent')) return;
    const headers = response.headers();
    let body = '';
    try { body = (await response.text()).slice(0, 500).replace(/("password"\s*:\s*")[^"]*/g, '$1<redacted>'); } catch {}
    sequence.push({ n: sequence.length + 1, phase: 'response', status: response.status(), set_cookie_names: String(headers['set-cookie'] || '').split(';').map((v) => v.split('=')[0].trim()).filter(Boolean), body });
  });
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(loginName);
  await inputs.nth(1).fill(PASSWORD);
  if (await inputs.nth(2).isEnabled()) {
    await inputs.nth(2).fill(DB_NAME);
  } else {
    requireCheck((await inputs.nth(2).inputValue()) === DB_NAME, 'configured login database mismatch');
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  try {
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  } catch (error) {
    console.error(`[browser-auth-sequence] ${JSON.stringify(sequence)}`);
    await page.screenshot({ path: path.join(OUTPUT_DIR, `login-failure-${loginName}.png`), fullPage: true });
    throw error;
  }
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
}

async function openAction(page, action) {
  const target = action.menuId > 0
    ? `/m/${action.menuId}?action_id=${action.actionId}`
    : `/a/${action.actionId}`;
  await page.goto(`${BASE_URL}${target}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  try {
    await page.locator('.layout-shell').waitFor({ timeout: 45000 });
    await page.locator('section.page[data-product-page-mode="list"]').first().waitFor({ timeout: 45000 });
    const loading = page.getByText('正在加载列表...', { exact: true }).last();
    if (await loading.count()) await loading.waitFor({ state: 'hidden', timeout: 45000 });
  } catch (error) {
    const html = await page.content();
    const visible = (await page.locator('body').innerText()).slice(0, 2000);
    const summary = await page.locator('section.page, table, [data-product-page-mode], [role="alert"]').evaluateAll((els) => els.slice(0, 30).map((el) => ({ tag: el.tagName, mode: el.getAttribute('data-product-page-mode'), text: (el.textContent || '').trim().slice(0, 240) })));
    await page.screenshot({ path: path.join(OUTPUT_DIR, 'payment-action-failure.png'), fullPage: true });
    fs.writeFileSync(path.join(OUTPUT_DIR, 'payment-action-failure.html'), html);
    fs.writeFileSync(path.join(OUTPUT_DIR, 'payment-action-failure.json'), JSON.stringify({ url: page.url(), title: await page.title(), visible, summary, action }, null, 2));
    console.error(`[payment-action-failure] ${JSON.stringify({ url: page.url(), title: await page.title(), visible, summary, action })}`);
    throw error;
  }
}

async function openScene(page, sceneKey) {
  await page.goto(`${BASE_URL}/s/${sceneKey}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
  await page.waitForFunction(() => {
    const text = document.body.innerText || '';
    return !text.includes('正在加载页面') && !text.includes('正在加载场景');
  }, null, { timeout: 45000 });
}

async function bodyText(page) {
  return page.locator('body').innerText();
}

async function selectCompany(page, companyName) {
  const selector = page.locator('label.business-scope-field select').filter({
    has: page.locator(`option:has-text("${companyName}")`),
  }).first();
  await selector.waitFor({ timeout: 30000 });
  await selector.selectOption({ label: companyName });
  await page.waitForTimeout(500);
  await page.waitForFunction((name) => {
    const select = [...document.querySelectorAll('label.business-scope-field select')]
      .find((node) => [...node.options].some((option) => option.textContent?.trim() === name));
    return select?.selectedOptions?.[0]?.textContent?.trim() === name;
  }, companyName, { timeout: 30000 });
}

async function waitForDenied(page) {
  await page.getByRole('heading', { name: '无权访问', exact: true }).waitFor({ timeout: 30000 });
  const text = await bodyText(page);
  requireCheck(text.includes('返回已授权的工作区'), 'permission denial lacks safe return guidance');
  requireCheck(!/records\s*=\s*0|可读降级渲染/.test(text), 'permission denial fell back to empty/read-only business page');
  return text;
}

async function logout(page) {
  await page.getByRole('button', { name: '退出登录' }).click();
  await page.waitForURL((url) => url.pathname.includes('/login'), { timeout: 30000 });
}

function actionableErrors(errors) {
  return errors.filter((line) => !line.includes('favicon') && !line.includes('ResizeObserver'));
}

async function main() {
  stage('S05 browser launch start');
  const browser = await launchChromium({ headless: true });
  stage('S06 browser launch complete');
  const result = { pass: false, base_url: BASE_URL, db: DB_NAME, checks: [], screenshots: [] };
  try {
    const finance = await browser.newPage({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
    stage('S07 finance page created');
    const financeErrors = [];
    let financeNav = [];
    const financeRequests = [];
    finance.on('request', (request) => {
      if (!request.url().includes('/api/v1/intent')) return;
      try { financeRequests.push(JSON.parse(request.postData() || '{}')); } catch {}
    });
    finance.on('response', async (response) => {
      if (!response.url().includes('/api/v1/intent')) return;
      try {
        const body = await response.json();
        const data = body?.result || body?.data || body;
        const d = data?.delivery_engine_v1?.nav;
        const r = data?.release_navigation_v1?.nav;
        if (Array.isArray(r)) financeNav = r;
        else if (Array.isArray(d)) financeNav = d;
        process.stderr.write(`[system-init-wire] status=${response.status()} delivery=${Array.isArray(d) ? d.length : 'missing'} release=${Array.isArray(r) ? r.length : 'missing'} result=${Array.isArray(data?.nav) ? data.nav.length : 'missing'}\n`);
      } catch {}
    });
    finance.on('console', (msg) => { if (msg.type() === 'error') financeErrors.push(msg.text()); });
    finance.on('pageerror', (error) => financeErrors.push(error.message));
    await login(finance, 'demo_role_finance');
    stage('S13 navigation complete');
    const financeNavText = JSON.stringify(financeNav);
    requireCheck(/payment\.request|付款|支付/.test(financeNavText), 'finance payment navigation was removed');
    requireCheck(/sc\.settlement\.order|结算/.test(financeNavText), 'finance settlement navigation was removed');
    requireCheck(PAYMENT_ACTION_ID > 0 && PAYMENT_MENU_ID > 0, 'fixture payment action context was not provided');
    const paymentAction = { actionId: PAYMENT_ACTION_ID, menuId: PAYMENT_MENU_ID };
    await openAction(finance, paymentAction);
    stage('S14 payment page open');
    await selectCompany(finance, 'FE Company A');
    await finance.waitForFunction(() => (document.body.innerText || '').includes('FE-A-PR-001'), null, { timeout: 45000 });
    let text = await bodyText(finance);
    requireCheck(text.includes('FE-A-PR-001') && text.includes('FE-B-PR-001'), 'finance company A payment rows missing');
    requireCheck(!text.includes('FE-C-PR-001'), 'finance company A leaked company B row');
    const financeA = path.join(OUTPUT_DIR, 'finance-company-a-payments.png');
    await finance.screenshot({ path: financeA, fullPage: true });
    result.screenshots.push(financeA);

    await selectCompany(finance, 'FE Company B');
    await finance.waitForFunction(() => (document.body.innerText || '').includes('FE-C-PR-001'), null, { timeout: 30000 });
    text = await bodyText(finance);
    requireCheck(text.includes('FE-C-PR-001'), 'finance company B payment row missing');
    requireCheck(!text.includes('FE-A-PR-001') && !text.includes('FE-B-PR-001'), 'finance company switch retained company A rows');
    const financeB = path.join(OUTPUT_DIR, 'finance-company-b-payments.png');
    await finance.screenshot({ path: financeB, fullPage: true });
    result.screenshots.push(financeB);
    const companyBInit = financeRequests.filter((row) => row?.intent === 'system.init').at(-1);
    requireCheck(Number(companyBInit?.params?.company_id || 0) > 0, 'company B system.init request lacks company_id context');
    await selectCompany(finance, 'FE Company A');
    await finance.waitForFunction(() => (document.body.innerText || '').includes('FE-A-PR-001'), null, { timeout: 30000 });
    text = await bodyText(finance);
    requireCheck(text.includes('FE-A-PR-001') && text.includes('FE-B-PR-001') && !text.includes('FE-C-PR-001'), 'finance company A rows did not recover after A-B-A switch');
    const companyAInit = financeRequests.filter((row) => row?.intent === 'system.init').at(-1);
    requireCheck(Number(companyAInit?.params?.company_id || 0) > 0 && companyAInit?.params?.company_id !== companyBInit?.params?.company_id, 'A-B-A request context reused the previous company');
    requireCheck(actionableErrors(financeErrors).length === 0, `finance browser errors: ${actionableErrors(financeErrors).join(' | ')}`);
    stage('S15 finance assertions');
    result.checks.push('finance_login', 'finance_navigation_preserved', 'finance_company_a_isolation', 'finance_company_b_switch_refresh', 'finance_company_a_switch_back', 'company_request_context_refresh');
    await finance.close();

    const member = await browser.newPage({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
    stage('S16 member page created');
    const memberErrors = [];
    let memberNav = [];
    member.on('console', (msg) => { if (msg.type() === 'error') memberErrors.push(msg.text()); });
    member.on('pageerror', (error) => memberErrors.push(error.message));
    member.on('response', async (response) => {
      if (!response.url().includes('/api/v1/intent')) return;
      try {
        const body = await response.json();
        const data = body?.result || body?.data || body;
        const nav = data?.release_navigation_v1?.nav || data?.delivery_engine_v1?.nav;
        if (Array.isArray(nav)) memberNav = nav;
      } catch {}
    });
    await login(member, 'demo_role_project_a_member');
    let shellText = await bodyText(member);
    requireCheck((await member.locator('.topbar-context').innerText()).includes('项目成员'), 'project member role label is not authoritative');
    const memberNavText = JSON.stringify(memberNav);
    fs.writeFileSync(path.join(OUTPUT_DIR, 'project-member-authority-nav.json'), `${JSON.stringify(memberNav, null, 2)}\n`);
    const memberSensitiveMatch = memberNavText.match(/财务中心|税务中心|人事行政|薪资福利|付款管理|结算管理|payment\.request|sc\.payment\.execution|sc\.settlement\.order/);
    requireCheck(!memberSensitiveMatch, `project member authority navigation contains sensitive entry: ${memberSensitiveMatch?.[0] || 'unknown'}`);
    await openScene(member, 'projects.list');
    await member.waitForFunction(() => (document.body.innerText || '').includes('FE Project A'), null, { timeout: 45000 });
    const memberText = await bodyText(member);
    requireCheck(memberText.includes('FE Project A'), 'project A member cannot see FE Project A');
    requireCheck(!memberText.includes('FE Project B') && !memberText.includes('FE Project C'), 'project A member sees out-of-scope project');
    const memberUnexpectedErrors = actionableErrors(memberErrors);
    requireCheck(memberUnexpectedErrors.length === 0, `member browser errors: ${memberUnexpectedErrors.join(' | ')}`);
    const memberShot = path.join(OUTPUT_DIR, 'project-a-member-projects.png');
    await member.screenshot({ path: memberShot, fullPage: true });
    result.screenshots.push(memberShot);
    requireCheck(PAYMENT_RECORD_A_ID > 0 && PAYMENT_RECORD_C_ID > 0, 'fixture payment record ids were not provided');
    const memberWire = [];
    member.on('response', async (response) => {
      if (!response.url().includes('/api/v1/intent')) return;
      let responseText = '';
      try { responseText = await response.text(); } catch {}
      memberWire.push({ status: response.status(), url: response.url(), body: responseText.slice(0, 2000) });
    });
    memberWire.length = 0;
    await member.goto(`${BASE_URL}/a/${PAYMENT_ACTION_ID}?menu_id=${PAYMENT_MENU_ID}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await waitForDenied(member);
    requireCheck(!memberWire.some((row) => /FE-[ABC]-PR-|1000\.0/.test(row.body)), 'sensitive action denial leaked record payload');
    const actionDenied = path.join(OUTPUT_DIR, 'project-member-action-denied.png');
    await member.screenshot({ path: actionDenied, fullPage: true }); result.screenshots.push(actionDenied);
    memberWire.length = 0;
    await member.goto(`${BASE_URL}/m/${PAYMENT_MENU_ID}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await waitForDenied(member);
    requireCheck(!memberWire.some((row) => /FE-[ABC]-PR-|1000\.0/.test(row.body)), 'sensitive menu denial leaked record payload');
    memberWire.length = 0;
    await member.goto(`${BASE_URL}/r/payment.request/${PAYMENT_RECORD_A_ID}?action_id=${PAYMENT_ACTION_ID}&menu_id=${PAYMENT_MENU_ID}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await waitForDenied(member);
    requireCheck(!memberWire.some((row) => /FE-A-PR-001|1000\.0/.test(row.body)), 'sensitive record route leaked project A payment payload');
    memberWire.length = 0;
    const outOfScopeDenied = member.waitForResponse(
      (response) => response.url().includes('/api/v1/intent') && response.status() === 403,
      { timeout: 30000 },
    );
    await member.goto(`${BASE_URL}/r/payment.request/${PAYMENT_RECORD_C_ID}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await outOfScopeDenied;
    await member.waitForFunction(() => /无权访问|无权限|权限不足|页面加载失败/.test(document.body.innerText || ''), null, { timeout: 30000 });
    shellText = await bodyText(member);
    requireCheck(!shellText.includes('FE-C-PR-001'), 'out-of-scope record title leaked on direct record route');
    requireCheck(memberWire.some((row) => row.status === 403), 'out-of-scope record route did not return HTTP 403');
    requireCheck(!memberWire.some((row) => /FE-C-PR-001|1000\.0/.test(row.body)), 'out-of-scope record response leaked sensitive payload');
    result.checks.push('project_a_member_login', 'project_member_role_label', 'project_member_sensitive_nav_absent', 'project_a_member_project_isolation', 'project_member_action_denied', 'project_member_menu_denied', 'project_member_sensitive_record_denied', 'project_member_out_of_scope_record_403', 'denial_payload_non_leakage');
    stage('S17 member assertions');
    await logout(member);
    await login(member, 'demo_role_pm');
    shellText = await bodyText(member);
    const pmRoleLabel = await member.locator('.topbar-context').innerText();
    requireCheck(/pm|负责人/i.test(pmRoleLabel) && !pmRoleLabel.includes('项目成员'), 'logout/login reused project member role surface for PM');
    result.checks.push('logout_login_role_cache_isolation', 'pm_login_and_navigation');
    await logout(member);
    await login(member, 'demo_role_owner');
    shellText = await bodyText(member);
    const ownerRoleLabel = await member.locator('.topbar-context').innerText();
    requireCheck(/业主|负责人|owner/i.test(ownerRoleLabel), `owner role surface changed or reused prior role cache: ${ownerRoleLabel}`);
    result.checks.push('owner_login_and_navigation');
    await member.close();
    result.journeys = {
      J02: {
        status: 'PASS',
        role: 'finance',
        steps: [
          { name: 'company_a', records: ['FE-A-PR-001', 'FE-A-PR-002', 'FE-B-PR-001'], screenshot: financeA },
          { name: 'company_b', records: ['FE-C-PR-001'], screenshot: financeB, company_id: companyBInit?.params?.company_id },
          { name: 'company_a_return', records: ['FE-A-PR-001', 'FE-A-PR-002', 'FE-B-PR-001'], company_id: companyAInit?.params?.company_id },
        ],
      },
      J03: {
        status: 'PASS',
        role: 'project_member',
        action_id: PAYMENT_ACTION_ID,
        menu_id: PAYMENT_MENU_ID,
        steps: [
          { name: 'role_and_navigation', status: 'PASS', screenshot: memberShot },
          { name: 'project_scope', visible: ['FE Project A'], hidden: ['FE Project B', 'FE Project C'] },
          { name: 'direct_action', status: 'PERMISSION_DENIED', url: `/a/${PAYMENT_ACTION_ID}?menu_id=${PAYMENT_MENU_ID}`, screenshot: actionDenied },
          { name: 'direct_menu', status: 'PERMISSION_DENIED', url: `/m/${PAYMENT_MENU_ID}` },
          { name: 'direct_sensitive_record', status: 'PERMISSION_DENIED', record_id: PAYMENT_RECORD_A_ID },
          { name: 'direct_out_of_scope_record', status: 403, record_id: PAYMENT_RECORD_C_ID },
        ],
      },
    };
    result.network_console = {
      finance_errors: actionableErrors(financeErrors),
      member_errors_before_expected_denial: memberUnexpectedErrors,
      sensitive_payload_leakage: false,
    };
    result.pass = true;
    stage('S18 report ready');
  } finally {
    stage('S19 browser close start');
    await browser.close();
    stage('S20 browser close complete');
    fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), `${JSON.stringify(result, null, 2)}\n`, 'utf8');
  }
  console.log('[verify.frontend.fixture.browser] PASS');
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(`[verify.frontend.fixture.browser] FAIL ${error.stack || error.message}`);
  process.exitCode = 2;
});
