#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { launchChromium } from './playwright_runtime.mjs';

const BASE_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const DB_NAME = process.env.DB_NAME || 'sc_frontend_acceptance';
const PASSWORD = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const OUTPUT_DIR = process.env.ARTIFACTS_DIR || 'artifacts/frontend-my-work-approval';
const TARGETS = JSON.parse(process.env.FRONTEND_MY_WORK_APPROVAL_TARGETS_JSON || '{}');
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

function check(value, message) { if (!value) throw new Error(message); }
function route(target) { return `/r/${target.model}/${target.record_id}?action_id=${target.action_id}&menu_id=${target.menu_id}`; }

function captureRuntime(page) {
  const state = { consoleErrors: [], pageErrors: [], responses: [] };
  page.on('console', (message) => {
    if (message.type() === 'error' && !/favicon|ResizeObserver/i.test(message.text())) state.consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => state.pageErrors.push(error.message));
  page.on('response', async (response) => {
    if (!response.url().includes('/api/v1/')) return;
    let intent = ''; let body = ''; let request = {};
    try { request = JSON.parse(response.request().postData() || '{}'); intent = request?.intent || ''; } catch {}
    if (response.status() < 400 && !['execute_button', 'payment.request.submit', 'payment.request.approve', 'payment.request.reject'].includes(intent)) return;
    try { body = (await response.text()).slice(0, 24000); } catch {}
    state.responses.push({ intent, status: response.status(), url: response.url(), request, body });
  });
  return state;
}

function resetRuntime(state) { state.consoleErrors.length = 0; state.pageErrors.length = 0; state.responses.length = 0; }
function assertClean(state, step, allowed = []) {
  const unexpected = state.responses.filter((row) => row.status >= 400 && !allowed.includes(row.status));
  check(!state.consoleErrors.length, `${step}: console errors ${state.consoleErrors.join(' | ')}`);
  check(!state.pageErrors.length, `${step}: page errors ${state.pageErrors.join(' | ')}`);
  check(!unexpected.length, `${step}: unexpected HTTP ${JSON.stringify(unexpected.map(({ intent, status }) => ({ intent, status })))}`);
}

async function login(page, user) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(user); await inputs.nth(1).fill(PASSWORD);
  if (await inputs.nth(2).isEnabled()) await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
}

async function logout(page) {
  await page.getByRole('button', { name: '退出登录' }).click();
  await page.waitForURL((url) => url.pathname.includes('/login'), { timeout: 30000 });
}

async function openMyWork(page) {
  await page.goto(`${BASE_URL}/my-work`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('.product-work').waitFor({ timeout: 45000 });
  check((await page.title()).endsWith(' - 智能施工企业管理平台'), `My Work document title invalid: ${await page.title()}`);
}

async function selectCompany(page, companyName) {
  const select = page.locator('label.business-scope-field select').filter({ has: page.locator(`option:has-text("${companyName}")`) }).first();
  await select.waitFor({ timeout: 30000 });
  const init = page.waitForResponse((response) => {
    if (!response.url().includes('/api/v1/intent')) return false;
    try { return JSON.parse(response.request().postData() || '{}')?.intent === 'system.init'; } catch { return false; }
  }, { timeout: 45000 });
  await select.selectOption({ label: companyName });
  await init;
  await page.waitForTimeout(300);
}

async function sectionCount(page, key) {
  return Number((await page.locator(`.count-card[data-section-key="${key}"] strong`).innerText()).trim());
}

async function assertCountMatches(page, key) {
  await page.locator(`.count-card[data-section-key="${key}"]`).click();
  const count = await sectionCount(page, key);
  const rows = await page.locator(`.work-section[data-section-key="${key}"] .work-card`).count();
  check(count === rows, `${key} count/list mismatch ${count}/${rows}`);
  return count;
}

async function noOverflow(page, label) {
  const size = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth }));
  check(size.scroll <= size.client + 1, `${label}: horizontal overflow ${size.scroll}/${size.client}`);
}

async function main() {
  for (const key of ['draft', 'approval', 'reject', 'completed', 'settlement', 'work_settlement']) check(TARGETS[key]?.record_id > 0, `missing target ${key}`);
  const browser = await launchChromium({ headless: true });
  const report = { pass: false, j07: {}, j08: {}, responsive: [], failure_paths: {}, isolation: {} };
  let page;
  let runtime;
  try {
    page = await browser.newPage({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
    runtime = captureRuntime(page);
    await login(page, 'demo_role_finance');
    resetRuntime(runtime);

    // J07: authoritative counts, detail round-trip, submit and company A/B/A invalidation.
    await openMyWork(page);
    const todoBefore = await assertCountMatches(page, 'todo');
    const initiatedBefore = await assertCountMatches(page, 'initiated');
    check(todoBefore > 0 && initiatedBefore > 0, 'J07 finance work sections are empty');
    await page.locator('.work-card').filter({ hasText: 'FE-JOURNEY-PAYMENT-001' }).getByRole('button', { name: '打开详情' }).click();
    await page.locator('.financial-workspace[data-workspace-kind="payment_request"]').waitFor({ timeout: 45000 });
    check((await page.locator('body').innerText()).includes('FE-JOURNEY-PAYMENT-001'), 'J07 detail identity missing');
    await page.goBack();
    await page.locator('.product-work').waitFor({ timeout: 45000 });
    await page.locator('.count-card[data-section-key="todo"]').click();
    const journeyCard = page.locator('.work-card').filter({ hasText: 'FE-JOURNEY-PAYMENT-001' });
    await journeyCard.getByRole('button', { name: '提交' }).click();
    const dialog = page.getByRole('dialog');
    await dialog.waitFor({ timeout: 15000 });
    const confirm = dialog.getByRole('button', { name: '确认提交' });
    check(await confirm.evaluate((node) => node === document.activeElement), 'J07 confirmation focus did not enter');
    await confirm.press('Enter');
    await page.waitForFunction(() => !(document.body.innerText || '').includes('FE-JOURNEY-PAYMENT-001') || !(document.querySelector('[data-section-key="todo"]')?.textContent || '').includes('FE-JOURNEY-PAYMENT-001'), null, { timeout: 45000 });
    await assertCountMatches(page, 'todo');
    await page.locator('.count-card[data-section-key="initiated"]').click();
    check(await page.locator('.work-card').filter({ hasText: 'FE-JOURNEY-PAYMENT-001' }).count() === 1, 'J07 submitted item left initiated section');
    await selectCompany(page, 'FE Company B');
    await openMyWork(page);
    check(!(await page.locator('body').innerText()).includes('FE-JOURNEY-PAYMENT-001'), 'J07 company B retained company A item');
    check((await page.locator('body').innerText()).includes('FE-C-PR-001'), 'J07 company B work item missing');
    await selectCompany(page, 'FE Company A');
    await openMyWork(page);
    check(!(await page.locator('body').innerText()).includes('FE-C-PR-001'), 'J07 company A retained company B item');
    assertClean(runtime, 'J07');
    report.j07 = { status: 'PASS', todo_before: todoBefore, initiated_before: initiatedBefore, company_a_b_a: 'PASS' };

    // J08 form: authoritative defaults, client required validation, save, refresh/edit and submit.
    resetRuntime(runtime);
    await page.goto(`${BASE_URL}${route(TARGETS.work_settlement)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.locator('.financial-workspace[data-workspace-kind="settlement"]').waitFor({ timeout: 45000 });
    await page.getByRole('button', { name: '新建付款申请' }).click();
    await page.waitForURL((url) => /\/(?:r|f)\/payment\.request\/new$/.test(url.pathname), { timeout: 45000 });
    const projectField = page.locator('[data-field-name="project_id"]');
    const contractField = page.locator('[data-field-name="contract_id"]');
    const settlementField = page.locator('[data-field-name="settlement_id"]');
    await projectField.waitFor({ timeout: 45000 });
    await page.waitForFunction(() => {
      const project = document.querySelector('[data-field-name="project_id"]')?.textContent || '';
      const contract = document.querySelector('[data-field-name="contract_id"]')?.textContent || '';
      const settlement = document.querySelector('[data-field-name="settlement_id"]')?.textContent || '';
      return project.includes('FE Project A') && !contract.includes('#') && settlement.includes('FE-B05-WORK-SETTLEMENT-001');
    }, null, { timeout: 45000 });
    check((await projectField.locator('input').inputValue()).includes('FE Project A'), 'J08 project default missing');
    check((await contractField.locator('input').inputValue()).trim().length > 0, 'J08 contract default missing');
    check((await settlementField.locator('input').inputValue()).includes('FE-B05-WORK-SETTLEMENT-001'), 'J08 settlement default missing');
    const amount = page.locator('[data-field-name="amount"] input').first();
    await amount.fill('');
    await page.getByRole('button', { name: '保存草稿' }).click();
    await page.locator('.validation-error, [role="alert"]').first().waitFor({ timeout: 15000 });
    check(page.url().includes('/new'), 'J08 invalid form created a record');
    report.failure_paths.required = 'PASS_DATA_UNCHANGED';
    await amount.fill('10.00');
    await page.getByRole('button', { name: '保存草稿' }).click();
    await page.waitForURL((url) => /\/(?:r|f)\/payment\.request\/\d+/.test(url.pathname), { timeout: 45000 });
    const createdUrl = page.url();
    const createdHeading = (await page.locator('h1.headline').innerText()).trim();
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.locator('.financial-workspace[data-workspace-kind="payment_request"]').waitFor({ timeout: 45000 });
    check((await page.locator('[data-field-name="amount"] input').inputValue()).includes('10'), 'J08 saved amount did not recover');
    const fileInput = page.locator('input[type="file"]').first();
    if (await fileInput.count()) await fileInput.setInputFiles({ name: 'fe-b05.txt', mimeType: 'text/plain', buffer: Buffer.from('FE-B05 form journey') });
    const submit = page.locator('.template-page-header-actions button').filter({ hasText: /^提交$/ }).first();
    await submit.waitFor({ timeout: 45000 });
    await submit.click();
    await page.getByRole('dialog').getByRole('button', { name: /^确认提交$/ }).click();
    await page.locator('.financial-workspace__status[data-state="submit"]').waitFor({ timeout: 15000 });
    const createdName = (await page.locator('h1.headline').innerText()).trim() || createdHeading;
    check(!createdName.includes('#'), `J08 technical created identity ${createdName}`);
    const createdIdentifier = createdName.match(/PRQ\d+/)?.[0] || createdName;
    await logout(page);

    await login(page, 'demo_role_executive');
    await openMyWork(page);
    await page.locator('.count-card[data-section-key="todo"]').click();
    const approvalCard = page.locator('.work-card').filter({ hasText: createdIdentifier }).first();
    await approvalCard.waitFor({ timeout: 45000 });
    await approvalCard.getByRole('button', { name: '审批' }).click();
    await page.getByRole('dialog').getByRole('button', { name: '确认审批' }).click();
    await page.waitForFunction((name) => !(document.body.innerText || '').includes(name), createdIdentifier, { timeout: 45000 });
    check(!(await page.locator('body').innerText()).includes(createdIdentifier), 'J08 approved item remained in todo');
    await logout(page);

    await login(page, 'demo_role_finance');
    await page.goto(createdUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.locator('.financial-workspace__status[data-state="approved"]').waitFor({ timeout: 45000 });
    check((await page.locator('body').innerText()).includes(createdIdentifier), 'J08 finance cannot see approved result');
    assertClean(runtime, 'J08');
    report.j08 = { status: 'PASS', created: createdName, save_refresh_edit_submit: 'PASS', executive_approval: 'PASS' };

    // Explicit reject validation and unauthorized isolation.
    await logout(page);
    await login(page, 'demo_role_executive');
    await openMyWork(page);
    await page.locator('.count-card[data-section-key="todo"]').click();
    const rejectCard = page.locator('.work-card').filter({ hasText: 'FE-JOURNEY-REJECT-001' });
    await rejectCard.getByRole('button', { name: '驳回' }).click();
    await page.getByRole('dialog').getByRole('button', { name: '确认驳回' }).click();
    await page.getByRole('alert').filter({ hasText: '拒绝原因' }).waitFor({ timeout: 10000 });
    check(await rejectCard.count() === 1, 'reject without reason changed work item');
    await page.getByRole('dialog').getByLabel('拒绝原因').fill('验收拒绝原因');
    await page.getByRole('dialog').getByRole('button', { name: '确认驳回' }).click();
    await page.waitForFunction(() => !(document.body.innerText || '').includes('FE-JOURNEY-REJECT-001'), null, { timeout: 45000 });
    report.failure_paths.reject_reason = 'PASS_DATA_UNCHANGED_BEFORE_VALID_REASON';
    await logout(page);

    await login(page, 'demo_role_project_a_member');
    await openMyWork(page);
    const memberText = await page.locator('body').innerText();
    check(!/FE-JOURNEY-(?:PAYMENT|APPROVAL|REJECT)|¥|￥/.test(memberText), 'project member My Work leaked payment facts');
    await page.goto(`${BASE_URL}${route(TARGETS.approval)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.getByRole('heading', { name: '无权访问', exact: true }).waitFor({ timeout: 45000 });
    const denied = await page.locator('body').innerText();
    check(!denied.includes('FE-JOURNEY-APPROVAL-001') && !denied.includes('80.00'), 'denial leaked approval facts');
    report.isolation.project_member = 'PASS';

    for (const viewport of [{ width: 1440, height: 900 }, { width: 1280, height: 800 }, { width: 390, height: 844 }]) {
      await page.setViewportSize(viewport);
      await openMyWork(page);
      await noOverflow(page, `${viewport.width}x${viewport.height}`);
      const screenshot = path.join(OUTPUT_DIR, `my-work-${viewport.width}x${viewport.height}.png`);
      await page.screenshot({ path: screenshot, fullPage: true });
      report.responsive.push({ viewport, status: 'PASS', screenshot });
    }
    await logout(page);
    report.pass = true;
    fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
    console.log('[verify.frontend.my_work_approval.browser] PASS');
  } catch (error) {
    if (page) await page.screenshot({ path: path.join(OUTPUT_DIR, 'failure.png'), fullPage: true }).catch(() => {});
    const pageState = page ? { url: page.url(), text: (await page.locator('body').innerText().catch(() => '')).slice(0, 12000) } : {};
    fs.writeFileSync(path.join(OUTPUT_DIR, 'failure.json'), `${JSON.stringify({ report, runtime, page: pageState, error: error.stack || error.message }, null, 2)}\n`);
    throw error;
  } finally {
    await browser.close();
  }
}

main().catch((error) => { console.error(`[verify.frontend.my_work_approval.browser] FAIL ${error.stack || error.message}`); process.exitCode = 1; });
