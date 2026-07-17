#!/usr/bin/env node
import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:18081';
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const OUT = path.resolve(process.cwd(), '../../../artifacts/playwright/low-code-safe-open');

function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).sort(([a], [b]) => a.localeCompare(b)).map(([key, item]) => [key, stable(item)]));
  }
  return value;
}

function hash(value) {
  return crypto.createHash('sha256').update(JSON.stringify(stable(value))).digest('hex');
}

function collectState(value) {
  let contractCount = 0;
  let versionCount = 0;
  let publishedCount = 0;
  const statuses = {};
  const visit = (item, key = '') => {
    if (Array.isArray(item)) {
      if (/contracts?$/i.test(key)) contractCount += item.length;
      if (/versions?$/i.test(key)) versionCount += item.length;
      item.forEach((child) => visit(child, key));
      return;
    }
    if (!item || typeof item !== 'object') return;
    if (item.published === true || item.status === 'published') publishedCount += 1;
    if (typeof item.status === 'string') statuses[item.status] = (statuses[item.status] || 0) + 1;
    Object.entries(item).forEach(([childKey, child]) => visit(child, childKey));
  };
  visit(value);
  return { payloadHash: hash(value), contractCount, versionCount, publishedCount, statuses };
}

async function login(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  if (await inputs.nth(2).isEnabled()) await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 60000 });
  await page.locator('.layout-shell').waitFor({ timeout: 60000 });
}

async function requestIntent(page, intent, params = {}) {
  return page.evaluate(async ({ dbName, intentName, intentParams }) => {
    const tokenEntry = Object.entries(sessionStorage).find(([key]) => key.startsWith('sc_auth_token:'));
    const token = String(tokenEntry?.[1] || '');
    if (!token) throw new Error('missing scoped auth token');
    const response = await fetch('/api/v1/intent', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'X-Odoo-DB': dbName,
        'X-Trace-Id': crypto.randomUUID(),
      },
      body: JSON.stringify({ intent: intentName, params: intentParams }),
    });
    const envelope = await response.json();
    if (!response.ok || envelope?.ok !== true) throw new Error(envelope?.error?.message || `snapshot export failed: ${response.status}`);
    return envelope.data;
  }, { dbName: DB_NAME, intentName: intent, intentParams: params });
}

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const observedIntents = [];
page.on('request', (request) => {
  if (!request.url().includes('/api/v1/intent') || request.method() !== 'POST') return;
  try { observedIntents.push(JSON.parse(request.postData() || '{}').intent || ''); } catch { observedIntents.push('UNPARSEABLE'); }
});

const report = { schema_version: 'low_code_safe_open_acceptance.v1', ok: false };
try {
  await login(page);
  const workbenchUrl = `${BASE_URL}/admin/business-config?db=${encodeURIComponent(DB_NAME)}&root_menu_xmlid=smart_construction_core.menu_sc_root&open_pages=1&model=construction.contract&action_id=1002&menu_id=389&page_label=${encodeURIComponent('合同办理')}`;
  await page.goto(workbenchUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('[data-lowcode-workbench-ia="three-column"]', { timeout: 60000 });
  await page.waitForFunction(() => document.querySelectorAll('.scan-row').length > 1, null, { timeout: 60000 });
  await page.locator('.business-config-context').getByRole('link', { name: '打开当前生效页面' }).waitFor({ state: 'visible', timeout: 60000 });
  const beforePayload = await requestIntent(page, 'ui.business_config.snapshot.export');
  const beforeMutationAudit = await requestIntent(page, 'ui.business_config.mutation_audit.snapshot');
  const beforeVersions = await requestIntent(page, 'ui.business_config.contract.versions', { model: 'construction.contract', action_id: 1002 });
  const before = { ...collectState(beforePayload), mutationAudit: beforeMutationAudit, versions: collectState(beforeVersions), versionCount: Number(beforeVersions?.version_count || 0) };
  const intentStart = observedIntents.length;
  const openButton = page.locator('.business-config-context').getByRole('link', { name: '打开当前生效页面' });
  const declaredRuntimeRoute = await page.locator('.business-config-page').getAttribute('data-runtime-route');
  const openButtonEnabled = await openButton.isEnabled();
  await openButton.click();
  await page.waitForTimeout(3000);
  if (new URL(page.url()).pathname === '/admin/business-config') {
    throw new Error(`current effective page did not navigate: ${page.url()} declared=${declaredRuntimeRoute} enabled=${openButtonEnabled}`);
  }
  await page.waitForSelector('main, [role="main"]', { timeout: 60000 });
  const openIntents = observedIntents.slice(intentStart);
  const runtimeUrl = page.url();
  await page.screenshot({ path: path.join(OUT, 'current-effective-page.png'), fullPage: true });
  await page.goto(workbenchUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('[data-lowcode-workbench-ia="three-column"]', { timeout: 60000 });
  await page.waitForFunction(() => document.querySelectorAll('.scan-row').length > 1, null, { timeout: 60000 });
  const afterPayload = await requestIntent(page, 'ui.business_config.snapshot.export');
  const afterMutationAudit = await requestIntent(page, 'ui.business_config.mutation_audit.snapshot');
  const afterVersions = await requestIntent(page, 'ui.business_config.contract.versions', { model: 'construction.contract', action_id: 1002 });
  const after = { ...collectState(afterPayload), mutationAudit: afterMutationAudit, versions: collectState(afterVersions), versionCount: Number(afterVersions?.version_count || 0) };
  const forbidden = openIntents.filter((intent) => /(?:save|publish|set|create|write|rollback|bootstrap|apply)/i.test(intent));
  report.before = before;
  report.after = after;
  report.runtime_url = runtimeUrl;
  report.open_intents = openIntents;
  report.forbidden_write_intents = forbidden;
  report.assertions = {
    runtime_route_opened: new URL(runtimeUrl).pathname === '/a/1002',
    payload_hash_unchanged: before.payloadHash === after.payloadHash,
    contract_count_unchanged: before.contractCount === after.contractCount,
    version_count_unchanged: before.versionCount === after.versionCount,
    version_payload_unchanged: before.versions.payloadHash === after.versions.payloadHash,
    published_state_unchanged: before.publishedCount === after.publishedCount,
    no_write_intent: forbidden.length === 0,
    formal_mutation_count_unchanged: before.mutationAudit.count === after.mutationAudit.count,
    formal_mutation_latest_id_unchanged: before.mutationAudit.latest_id === after.mutationAudit.latest_id,
  };
  report.ok = Object.values(report.assertions).every(Boolean);
} catch (error) {
  report.failure = error instanceof Error ? error.message : String(error);
} finally {
  await browser.close();
  await fs.writeFile(path.join(OUT, 'report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8');
}

if (!report.ok) {
  console.error('[low_code_safe_open_acceptance] FAIL', report.failure || report.assertions);
  process.exit(1);
}
console.log(`[low_code_safe_open_acceptance] PASS hash=${report.before.payloadHash} contracts=${report.before.contractCount} versions=${report.before.versionCount}`);
