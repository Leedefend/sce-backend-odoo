#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { launchChromium } from './playwright_runtime.mjs';

const BASE_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const DB_NAME = process.env.DB_NAME || 'sc_frontend_acceptance';
const PASSWORD = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const TARGETS = JSON.parse(process.env.FRONTEND_DELIVERY_HARDENING_TARGETS_JSON || '{}');
const OUT = process.env.ARTIFACTS_DIR || 'artifacts/frontend-shell-usability';

if (!/^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i.test(BASE_URL)) {
  throw new Error(`frontend shell usability browser requires loopback URL, got ${BASE_URL}`);
}
if (DB_NAME !== 'sc_frontend_acceptance') {
  throw new Error(`frontend shell usability browser requires sc_frontend_acceptance, got ${DB_NAME}`);
}

fs.mkdirSync(path.join(OUT, 'screenshots'), { recursive: true });

function check(value, message) {
  if (!value) throw new Error(message);
}

function listRoute(target) {
  return `/a/${target.action_id}?menu_id=${target.menu_id}&action_id=${target.action_id}&view_mode=tree`;
}

function recordRoute(target) {
  return `/r/${target.model}/${target.record_id}?action_id=${target.action_id}&menu_id=${target.menu_id}`;
}

async function login(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('#login-username').fill('demo_role_finance');
  await page.locator('#login-password').fill(PASSWORD);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
}

function observe(page) {
  const state = { console: [], pageerror: [], http: [] };
  page.on('console', (message) => {
    if (message.type() === 'error' && !/favicon|ResizeObserver/i.test(message.text())) state.console.push(message.text());
  });
  page.on('pageerror', (error) => state.pageerror.push(error.message));
  page.on('response', (response) => {
    if (response.status() >= 400 && response.url().includes('/api/v1/')) state.http.push(response.status());
  });
  return state;
}

async function noPageOverflow(page, label) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  check(overflow === 0, `${label}: page horizontal overflow=${overflow}`);
}

const browser = await launchChromium({ headless: true });
const report = { desktop: {}, mobile: {}, errors: [] };
try {
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const desktopRuntime = observe(desktop);
  await login(desktop);
  await desktop.goto(`${BASE_URL}${listRoute(TARGETS.payment_request)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await desktop.locator('table.flat-table').waitFor({ timeout: 45000 });
  const createBox = await desktop.getByRole('button', { name: '新建', exact: true }).boundingBox();
  check(createBox && createBox.x + createBox.width <= 1440, 'desktop: create action clipped outside viewport');
  check(await desktop.locator('h1').count() === 1, 'desktop list: expected one h1');
  await noPageOverflow(desktop, 'desktop list');
  await desktop.screenshot({ path: path.join(OUT, 'screenshots', 'list-desktop.png'), fullPage: true });

  await desktop.goto(`${BASE_URL}${recordRoute(TARGETS.payment_request)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await desktop.locator('.financial-workspace').waitFor({ timeout: 45000 });
  check(await desktop.locator('h1').count() === 1, 'desktop detail: expected one h1');
  await noPageOverflow(desktop, 'desktop detail');

  await desktop.goto(`${BASE_URL}${recordRoute(TARGETS.work_settlement)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await desktop.locator('.financial-workspace[data-workspace-kind="settlement"]').waitFor({ timeout: 45000 });
  await desktop.getByRole('button', { name: '新建付款申请' }).click();
  await desktop.locator('[data-field-name="amount"]').waitFor({ timeout: 45000 });
  check(await desktop.locator('h1').count() === 1, 'desktop form: expected one h1');
  await noPageOverflow(desktop, 'desktop form');
  report.desktop = { list: 'PASS', detail: 'PASS', form: 'PASS', create_action_visible: true };
  await desktop.close();

  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const mobileRuntime = observe(mobile);
  await login(mobile);
  await mobile.goto(`${BASE_URL}${listRoute(TARGETS.payment_request)}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await mobile.locator('.mobile-record-card').first().waitFor({ timeout: 45000 });
  check(await mobile.locator('#primary-sidebar').count() === 0, 'mobile: sidebar must be closed initially');
  check(await mobile.locator('.mobile-record-card').count() > 0, 'mobile: record cards missing');
  check(!(await mobile.locator('table.flat-table').isVisible()), 'mobile: desktop table should be hidden');
  await noPageOverflow(mobile, 'mobile list');
  await mobile.screenshot({ path: path.join(OUT, 'screenshots', 'list-mobile.png'), fullPage: true });
  await mobile.getByRole('button', { name: '菜单', exact: true }).click();
  await mobile.locator('#primary-sidebar').waitFor({ timeout: 5000 });
  check(await mobile.locator('.shell--mobile-sidebar-open').count() === 1, 'mobile: navigation drawer did not open');
  await mobile.keyboard.press('Escape');
  await mobile.locator('#primary-sidebar').waitFor({ state: 'detached', timeout: 5000 });
  await mobile.locator('.mobile-record-card').first().click();
  await mobile.waitForURL((url) => url.pathname.startsWith('/r/'), { timeout: 45000 });
  await mobile.locator('.financial-workspace').waitFor({ timeout: 45000 });
  check(await mobile.locator('h1').count() === 1, 'mobile detail: expected one h1');
  await noPageOverflow(mobile, 'mobile detail');
  await mobile.screenshot({ path: path.join(OUT, 'screenshots', 'detail-mobile.png'), fullPage: true });
  await mobile.getByRole('button', { name: '我的工作', exact: true }).click();
  await mobile.locator('.product-work').waitFor({ timeout: 45000 });
  await mobile.locator('.count-card[data-section-key="todo"]').press('Enter');
  const workCard = mobile.locator('.work-section[data-section-key="todo"] .work-card').filter({ hasText: 'FE-JOURNEY-PAYMENT-001' });
  const workDetailButton = workCard.getByRole('button', { name: '打开详情' });
  await workDetailButton.focus();
  await workDetailButton.press('Enter');
  await mobile.waitForURL((url) => url.pathname.startsWith('/r/payment.request/'), { timeout: 45000 });
  await mobile.locator('.financial-workspace[data-workspace-kind="payment_request"]').waitFor({ timeout: 45000 }).catch(() => {
    throw new Error(`mobile My Work detail did not load, url=${mobile.url()}`);
  });
  await mobile.getByText('FE-JOURNEY-PAYMENT-001', { exact: false }).first().waitFor({ timeout: 45000 });
  report.mobile = { drawer: 'PASS', cards: 'PASS', detail: 'PASS', my_work_detail: 'PASS', horizontal_overflow: 0 };
  report.errors = [...desktopRuntime.console, ...desktopRuntime.pageerror, ...desktopRuntime.http, ...mobileRuntime.console, ...mobileRuntime.pageerror, ...mobileRuntime.http];
  check(report.errors.length === 0, `browser runtime errors: ${JSON.stringify(report.errors)}`);
  await mobile.close();
} finally {
  await browser.close();
}

fs.writeFileSync(path.join(OUT, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
console.log(`FRONTEND_SHELL_USABILITY=${JSON.stringify(report)}`);
