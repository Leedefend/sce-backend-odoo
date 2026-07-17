#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:18081';
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const OUT = path.resolve(process.cwd(), '../../../artifacts/playwright/low-code-workbench-faults');
const WORKBENCH = `${BASE_URL}/admin/business-config?db=${encodeURIComponent(DB_NAME)}&root_menu_xmlid=smart_construction_core.menu_sc_root&open_pages=1&model=construction.contract&action_id=1002&page_label=${encodeURIComponent('合同办理')}`;
const CASES = [
  { key: 'bad_request', status: 400, code: 'INVALID_PARAMS' },
  { key: 'session_expired', status: 401, code: 'UNAUTHORIZED' },
  { key: 'conflict', status: 409, code: 'CONFLICT' },
  { key: 'validation', status: 422, code: 'VALIDATION_ERROR' },
  { key: 'server_error', status: 500, code: 'INTERNAL_ERROR' },
  { key: 'network_failure', status: 0, code: 'NETWORK_FAILURE' },
];

async function login(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const inputs = page.locator('input');
  await inputs.nth(0).fill('wutao'); await inputs.nth(1).fill('123456');
  if (await inputs.nth(2).isEnabled()) await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 60000 });
  await page.locator('.layout-shell').waitFor({ timeout: 60000 });
}

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true });
const report = { schema_version: 'low_code_workbench_fault_acceptance.v1', ok: false, cases: [] };
try {
  for (const fault of CASES) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    const runtime = { console: [], pageerror: [] };
    page.on('console', (message) => { if (message.type() === 'error' && !(fault.status >= 400 && message.text().includes(String(fault.status)))) runtime.console.push(message.text()); });
    page.on('pageerror', (error) => runtime.pageerror.push(error.message));
    await login(page);
    let injected = false;
    await page.route('**/api/v1/intent*', async (route) => {
      let intent = '';
      try { intent = JSON.parse(route.request().postData() || '{}').intent || ''; } catch { /* pass through */ }
      if (!injected && intent === 'ui.business_config.surface.get') {
        injected = true;
        if (!fault.status) return route.abort('failed');
        return route.fulfill({
          status: fault.status,
          contentType: 'application/json',
          body: JSON.stringify({ ok: false, error: { code: fault.code, reason_code: fault.code, message: `${fault.key} injected`, retryable: fault.status >= 500 }, meta: { trace_id: `lc-pro-01-${fault.key}` } }),
        });
      }
      return route.continue();
    });
    await page.goto(WORKBENCH, { waitUntil: 'domcontentloaded', timeout: 60000 });
    if (fault.status === 401) {
      await page.waitForURL((url) => url.pathname === '/login', { timeout: 60000 });
      report.cases.push({ key: fault.key, injected, redirectedToLogin: true, finalUrl: page.url(), runtime });
    } else {
      await page.waitForSelector('.status.error', { timeout: 60000 });
      const errorText = await page.locator('.status.error').innerText();
      await page.locator('.business-config-context').getByRole('button', { name: '选择业务页面' }).click();
      await page.waitForSelector('[data-lowcode-workbench-ia="three-column"]', { timeout: 60000 });
      await page.waitForSelector('.status.error', { state: 'detached', timeout: 60000 });
      report.cases.push({ key: fault.key, injected, errorText, retryRecovered: true, finalUrl: page.url(), runtime });
    }
    await page.screenshot({ path: path.join(OUT, `${fault.key}.png`), fullPage: true });
    await context.close();
  }
  report.assertions = {
    six_faults_covered: report.cases.length === 6,
    session_expired_to_login: report.cases.find((row) => row.key === 'session_expired')?.redirectedToLogin === true,
    recoverable_faults_retry: report.cases.filter((row) => row.key !== 'session_expired').every((row) => row.retryRecovered === true),
    no_pageerror: report.cases.every((row) => row.runtime.pageerror.length === 0),
  };
  report.ok = Object.values(report.assertions).every(Boolean);
} catch (error) {
  report.failure = error instanceof Error ? error.message : String(error);
} finally {
  await browser.close();
  await fs.writeFile(path.join(OUT, 'report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8');
}

if (!report.ok) { console.error('[low_code_workbench_fault_acceptance] FAIL', report.failure || report.assertions); process.exit(1); }
console.log('[low_code_workbench_fault_acceptance] PASS 400/401/409/422/500/network');
