#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { launchChromium } from './playwright_runtime.mjs';

const BASE_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const DB_NAME = process.env.DB_NAME || 'sc_frontend_acceptance';
const PASSWORD = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const TARGETS = JSON.parse(process.env.FRONTEND_FINANCIAL_WORKSPACE_TARGETS_JSON || '{}');
const OUTPUT = process.env.ARTIFACTS_DIR || 'artifacts/frontend-professional/fe-pro-03/journeys';
const JOURNEY = String(process.env.FE_PRO_03_JOURNEY || 'all').trim().toUpperCase();
fs.mkdirSync(OUTPUT, { recursive: true });

function check(value, message) {
  if (!value) throw new Error(message);
}

function formRoute(target) {
  return `/f/${encodeURIComponent(target.model)}/${target.record_id}?action_id=${target.action_id}&menu_id=${target.menu_id}`;
}

function recordRoute(target) {
  return `/r/${encodeURIComponent(target.model)}/${target.record_id}?action_id=${target.action_id}&menu_id=${target.menu_id}`;
}

function capture(page) {
  const runtime = { console: [], pageerror: [], unexpectedHttp: [] };
  page.on('console', (message) => {
    if (message.type() === 'error' && !/favicon|ResizeObserver|Failed to load resource/i.test(message.text())) runtime.console.push(message.text());
  });
  page.on('pageerror', (error) => runtime.pageerror.push(error.message));
  page.on('response', (response) => {
    if (response.status() >= 400 && response.status() !== 409) {
      let payload = {};
      try { payload = JSON.parse(response.request().postData() || '{}'); } catch {}
      runtime.unexpectedHttp.push({ status: response.status(), url: response.url(), intent: payload?.intent || '', params: payload?.params || {} });
    }
  });
  return runtime;
}

async function login(page, loginName) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(loginName);
  await inputs.nth(1).fill(PASSWORD);
  if (await inputs.nth(2).isEnabled().catch(() => false)) await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
}

async function waitForm(page) {
  await page.locator('[data-product-page-mode="form"]').waitFor({ timeout: 45000 });
  await page.waitForFunction(() => !(document.querySelector('main')?.textContent || '').includes('正在加载'), null, { timeout: 45000 });
}

async function j12(page) {
  const target = TARGETS.contract;
  await page.goto(`${BASE_URL}${formRoute(target)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForm(page);
  const subject = page.locator('[data-field-name="subject"] input, [data-field-name="subject"] textarea').first();
  await subject.waitFor({ timeout: 30000 });
  check(await subject.isEditable(), 'J12 contract subject is not editable for PM');
  const original = await subject.inputValue();
  const edited = `${original} · J12`;
  await subject.fill(edited);
  await page.getByRole('button', { name: '放弃', exact: true }).waitFor({ timeout: 15000 });
  const back = page.getByRole('button', { name: '返回列表', exact: true });
  await back.click();
  const leaveDialog = page.getByRole('dialog');
  await leaveDialog.waitFor({ timeout: 15000 });
  check((await leaveDialog.innerText()).includes('尚未保存'), 'J12 unsaved warning missing');
  await leaveDialog.getByRole('button', { name: '取消', exact: true }).click();
  check(await subject.inputValue() === edited, 'J12 cancel leave discarded the current input');
  const save = page.getByRole('button', { name: /^保存$/ }).first();
  await save.click();
  await page.getByText(/保存成功|已保存/, { exact: false }).first().waitFor({ timeout: 45000 });
  await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForm(page);
  const persisted = await page.locator('[data-field-name="subject"] input, [data-field-name="subject"] textarea').first().inputValue();
  check(persisted === edited, `J12 authoritative reload mismatch: ${persisted}`);
  return { status: 'PASS', role: 'pm', dirty_guard: true, cancel_retains_input: true, save_and_reload: true };
}

async function openLegalPaymentCreate(page) {
  await page.goto(`${BASE_URL}${recordRoute(TARGETS.settlement)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  const workspace = page.locator('.financial-workspace[data-workspace-kind="settlement"]');
  await workspace.waitFor({ timeout: 45000 });
  await workspace.getByRole('button', { name: '新建付款申请', exact: true }).click();
  await page.waitForURL((url) => url.pathname.includes('/f/payment.request/new'), { timeout: 45000 });
  await waitForm(page);
}

async function interceptWriteConflict(page) {
  let intercepted = 0;
  const handler = async (route) => {
    let payload = {};
    try { payload = JSON.parse(route.request().postData() || '{}'); } catch {}
    const params = payload?.params || {};
    if (!intercepted && payload?.intent === 'api.data' && params?.op === 'write' && params?.model === 'payment.request') {
      intercepted += 1;
      await route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({ ok: false, code: 409, error: { code: 'CONFLICT', reason_code: 'CONFLICT', message: 'record changed' } }),
      });
      return;
    }
    await route.continue();
  };
  await page.route('**/api/v1/intent**', handler);
  return async () => {
    await page.unroute('**/api/v1/intent**', handler);
    return intercepted;
  };
}

async function j13(page) {
  await openLegalPaymentCreate(page);
  const amount = page.locator('[data-field-name="amount"] input').first();
  await amount.waitFor({ timeout: 30000 });
  await amount.fill('');
  await page.getByRole('button', { name: '保存草稿', exact: true }).click();
  const summary = page
    .getByRole('alert')
    .filter({ has: page.getByRole('heading', { name: '请检查以下内容', exact: true }) });
  await summary.waitFor({ timeout: 15000 });
  const firstError = summary.locator('button').first();
  await firstError.click();
  check(await amount.evaluate((node) => node === document.activeElement), 'J13 error summary did not focus amount');

  await page.goto(`${BASE_URL}${formRoute(TARGETS.journey_request)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForm(page);
  const existingAmount = page.locator('[data-field-name="amount"] input').first();
  await existingAmount.waitFor({ timeout: 30000 });
  const authorityValue = await existingAmount.inputValue();
  const localValue = String(Number(authorityValue || 0) + 1);
  await existingAmount.fill(localValue);
  const removeConflict = await interceptWriteConflict(page);
  await page.getByRole('button', { name: /^保存(?:草稿)?$/ }).first().click();
  await page.getByRole('heading', { name: '记录已被其他操作更新' }).waitFor({ timeout: 30000 });
  check(await existingAmount.inputValue() === localValue, 'J13 conflict did not retain local input');
  const intercepted = await removeConflict();
  check(intercepted === 1, `J13 expected one write conflict, got ${intercepted}`);
  await page.getByRole('button', { name: '加载最新数据', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog.waitFor({ timeout: 15000 });
  await dialog.getByRole('button', { name: '确认加载最新数据', exact: true }).click();
  await page.waitForFunction((value) => {
    const input = document.querySelector('[data-field-name="amount"] input');
    return input instanceof HTMLInputElement && input.value === value;
  }, authorityValue, { timeout: 45000 });
  return { status: 'PASS', required_error_focus: true, conflict_retains_input: true, authoritative_reload: true };
}

async function main() {
  check(TARGETS.contract?.record_id > 0 && TARGETS.settlement?.record_id > 0 && TARGETS.journey_request?.record_id > 0, 'missing J12/J13 targets');
  const browser = await launchChromium({ headless: true });
  const report = { schema_version: 'frontend_core_record_form_journeys.v1', database: DB_NAME, j12: {}, j13: {}, runtime: {}, pass: false };
  try {
    let context;
    let page;
    const j12Runtime = { console: [], pageerror: [], unexpectedHttp: [] };
    const j13Runtime = { console: [], pageerror: [], unexpectedHttp: [] };
    if (JOURNEY === 'ALL' || JOURNEY === 'J12') {
      context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
      page = await context.newPage();
      Object.assign(j12Runtime, capture(page));
      await login(page, 'demo_role_pm');
      report.j12 = await j12(page);
      await context.close();
    }
    if (JOURNEY === 'ALL' || JOURNEY === 'J13') {
      context = await browser.newContext({ viewport: { width: 390, height: 844 }, locale: 'zh-CN' });
      page = await context.newPage();
      Object.assign(j13Runtime, capture(page));
      await login(page, 'demo_role_finance');
      report.j13 = await j13(page);
      await page.screenshot({ path: path.join(OUTPUT, 'j13-recovered-390x844.png'), fullPage: true });
      await context.close();
    }
    report.runtime = { j12: j12Runtime, j13: j13Runtime };
    check(!j12Runtime.console.length && !j12Runtime.pageerror.length && !j12Runtime.unexpectedHttp.length, `J12 runtime errors ${JSON.stringify(j12Runtime)}`);
    check(!j13Runtime.console.length && !j13Runtime.pageerror.length && !j13Runtime.unexpectedHttp.length, `J13 runtime errors ${JSON.stringify(j13Runtime)}`);
    report.pass = true;
    fs.writeFileSync(path.join(OUTPUT, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
    console.log('[verify.frontend.core_record_form.journeys] PASS J12 J13');
  } catch (error) {
    fs.writeFileSync(path.join(OUTPUT, 'failure.json'), `${JSON.stringify({ ...report, error: error.stack || error.message }, null, 2)}\n`);
    throw error;
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(`[verify.frontend.core_record_form.journeys] FAIL ${error.stack || error.message}`);
  process.exitCode = 1;
});
