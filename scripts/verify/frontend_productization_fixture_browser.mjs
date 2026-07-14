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
    finance.on('console', (msg) => { if (msg.type() === 'error') financeErrors.push(msg.text()); });
    finance.on('pageerror', (error) => financeErrors.push(error.message));
    await login(finance, 'demo_role_finance');
    stage('S13 navigation complete');
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
    requireCheck(actionableErrors(financeErrors).length === 0, `finance browser errors: ${actionableErrors(financeErrors).join(' | ')}`);
    stage('S15 finance assertions');
    result.checks.push('finance_login', 'finance_company_a_isolation', 'finance_company_b_switch_refresh');
    await finance.close();

    const member = await browser.newPage({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
    stage('S16 member page created');
    const memberErrors = [];
    member.on('console', (msg) => { if (msg.type() === 'error') memberErrors.push(msg.text()); });
    member.on('pageerror', (error) => memberErrors.push(error.message));
    await login(member, 'demo_role_project_a_member');
    await openScene(member, 'projects.list');
    await member.waitForFunction(() => (document.body.innerText || '').includes('FE Project A'), null, { timeout: 45000 });
    const memberText = await bodyText(member);
    requireCheck(memberText.includes('FE Project A'), 'project A member cannot see FE Project A');
    requireCheck(!memberText.includes('FE Project B') && !memberText.includes('FE Project C'), 'project A member sees out-of-scope project');
    requireCheck(actionableErrors(memberErrors).length === 0, `member browser errors: ${actionableErrors(memberErrors).join(' | ')}`);
    const memberShot = path.join(OUTPUT_DIR, 'project-a-member-projects.png');
    await member.screenshot({ path: memberShot, fullPage: true });
    result.screenshots.push(memberShot);
    result.checks.push('project_a_member_login', 'project_a_member_project_isolation');
    stage('S17 member assertions');
    await member.close();
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
