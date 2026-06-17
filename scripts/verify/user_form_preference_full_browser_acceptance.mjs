#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { launchChromium } from './playwright_runtime.mjs';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const baseUrl = process.env.BASE_URL || 'http://127.0.0.1:18081';
const dbName = process.env.DB_NAME || process.env.DB || 'sc_demo';
const loginName = process.env.E2E_LOGIN || process.env.LOGIN || 'wutao';
const password = process.env.E2E_PASSWORD || process.env.PASSWORD || '123456';
const targetsPath = path.resolve(process.env.USER_FORM_TARGETS_PATH || '/tmp/dev_user_form_targets.json');
const artifactRoot = path.resolve(
  repoRoot,
  process.env.USER_FORM_BROWSER_ARTIFACT_ROOT || 'artifacts/playwright/user-form-preference-full-browser',
);
const reportPath = path.join(artifactRoot, 'report.json');
const routeTimeoutMs = Number(process.env.USER_FORM_BROWSER_ROUTE_TIMEOUT_MS || 90000);
const limit = Number(process.env.USER_FORM_BROWSER_LIMIT || 0);

function asPositiveInt(value) {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : 0;
}

function recordUrl(target) {
  const model = String(target.model || '').trim();
  const recId = asPositiveInt(target.rec_id || target.record_id || target.id);
  const actionId = asPositiveInt(target.action_id);
  const menuId = asPositiveInt(target.menu_id);
  const url = new URL(`/r/${encodeURIComponent(model)}/${recId}`, baseUrl);
  if (actionId) url.searchParams.set('action_id', String(actionId));
  if (menuId) url.searchParams.set('menu_id', String(menuId));
  url.searchParams.set('db', dbName);
  return url.toString();
}

async function login(page) {
  await page.goto(`${baseUrl}/login?db=${encodeURIComponent(dbName)}`, {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  });
  await page.locator('input').nth(0).fill(loginName);
  await page.locator('input[type="password"]').fill(password);
  if (await page.locator('input').count() >= 3) {
    await page.locator('input').nth(2).fill(dbName).catch(() => {});
  }
  await page.locator('button[type="submit"]').click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 60000 });
}

async function validateTarget(page, target, index) {
  const startedAt = Date.now();
  const failures = [];
  const badResponses = [];
  const consoleErrors = [];
  const intentRequests = [];
  const url = recordUrl(target);

  const onResponse = async (response) => {
    if (!response.url().includes('/api/v1/intent') || response.status() < 400) return;
    let body = '';
    try {
      body = (await response.text()).slice(0, 800);
    } catch {
      body = '';
    }
    badResponses.push({ status: response.status(), body });
  };
  const onRequest = (request) => {
    if (!request.url().includes('/api/v1/intent')) return;
    intentRequests.push((request.postData() || '').slice(0, 600));
  };
  const onConsole = (message) => {
    if (message.type() !== 'error') return;
    consoleErrors.push(message.text().slice(0, 800));
  };
  const onPageError = (error) => {
    consoleErrors.push(error.message.slice(0, 800));
  };

  page.on('response', onResponse);
  page.on('request', onRequest);
  page.on('console', onConsole);
  page.on('pageerror', onPageError);

  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForFunction(() => {
      const text = String(document.body?.innerText || '');
      const hasNativeForm = document.querySelectorAll('.native-form-tree').length > 0;
      const hasRuntimeError = /页面加载失败|Request failed|BAD_REQUEST|Traceback|Cannot read/i.test(text);
      return hasRuntimeError || (hasNativeForm && !text.includes('正在加载页面'));
    }, null, { timeout: routeTimeoutMs }).catch(() => {});
    await page.waitForTimeout(500);
    const snapshot = await page.evaluate(() => {
      const text = String(document.body?.innerText || '').replace(/\s+/g, ' ').trim();
      const nativeTrees = document.querySelectorAll('.native-form-tree').length;
      const inputs = document.querySelectorAll('input, textarea, select').length;
      const gridColumns = Array.from(document.querySelectorAll('.native-form-tree [style*="grid-template-columns"]'))
        .map((node) => window.getComputedStyle(node).gridTemplateColumns)
        .filter(Boolean)
        .slice(0, 12);
      return {
        text: text.slice(0, 1600),
        loading: text.includes('正在加载页面'),
        runtimeError: /页面加载失败|Request failed|BAD_REQUEST|Traceback|Cannot read/i.test(text),
        nativeTrees,
        inputs,
        gridColumns,
      };
    });
    if (page.url().includes('/login')) failures.push('redirected to login');
    if (!snapshot.text) failures.push('empty body');
    if (snapshot.loading) failures.push('still loading');
    if (snapshot.runtimeError) failures.push('visible runtime error');
    if (!snapshot.nativeTrees) failures.push('missing native form tree');
    if (badResponses.length) failures.push(`bad intent responses: ${badResponses.map((row) => row.status).join(',')}`);
    if (consoleErrors.length) failures.push(`console errors: ${consoleErrors.length}`);
    if (String(target.model || '') === 'sc.business.entity' && snapshot.text.includes('旧主体映射')) {
      failures.push('internal map field visible');
    }
    const mapRequestCount = intentRequests.filter((text) => text.includes('sc.legacy.business.entity.map') || text.includes('map_ids')).length;
    if (String(target.model || '') === 'sc.business.entity' && mapRequestCount) {
      failures.push('internal map model requested');
    }
    return {
      index,
      ok: failures.length === 0,
      elapsed_ms: Date.now() - startedAt,
      target,
      url,
      failures,
      bad_responses: badResponses,
      console_errors: consoleErrors,
      intent_request_count: intentRequests.length,
      map_request_count: mapRequestCount,
      snapshot,
    };
  } catch (error) {
    return {
      index,
      ok: false,
      elapsed_ms: Date.now() - startedAt,
      target,
      url,
      failures: [error instanceof Error ? error.message : String(error)],
      bad_responses: badResponses,
      console_errors: consoleErrors,
      intent_request_count: intentRequests.length,
      map_request_count: 0,
      snapshot: {},
    };
  } finally {
    page.off('response', onResponse);
    page.off('request', onRequest);
    page.off('console', onConsole);
    page.off('pageerror', onPageError);
  }
}

async function main() {
  await fs.mkdir(artifactRoot, { recursive: true });
  const loaded = JSON.parse(await fs.readFile(targetsPath, 'utf8'));
  const targets = (Array.isArray(loaded) ? loaded : []).filter((target) => (
    String(target.model || '').trim()
    && asPositiveInt(target.rec_id || target.record_id || target.id)
    && asPositiveInt(target.action_id)
  ));
  const selectedTargets = limit > 0 ? targets.slice(0, limit) : targets;
  if (!selectedTargets.length) {
    throw new Error(`no form targets found: ${targetsPath}`);
  }

  const browser = await launchChromium({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: 'zh-CN' });
  await login(page);

  const results = [];
  for (let index = 0; index < selectedTargets.length; index += 1) {
    const result = await validateTarget(page, selectedTargets[index], index + 1);
    results.push(result);
    if ((index + 1) % 10 === 0 || !result.ok || index === selectedTargets.length - 1) {
      const failed = results.filter((row) => !row.ok).length;
      const target = selectedTargets[index];
      console.log(`[user_form_browser] ${index + 1}/${selectedTargets.length} failed=${failed} ${result.ok ? 'PASS' : 'FAIL'} ${target.title || target.model}`);
    }
  }

  await browser.close();
  const failures = results.filter((row) => !row.ok);
  const report = {
    ok: failures.length === 0,
    base_url: baseUrl,
    db_name: dbName,
    login: loginName,
    targets_path: targetsPath,
    target_count: selectedTargets.length,
    failure_count: failures.length,
    failures,
    results,
  };
  await fs.writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  if (!report.ok) {
    console.error(JSON.stringify({
      ok: false,
      target_count: report.target_count,
      failure_count: report.failure_count,
      report_path: reportPath,
      failures: failures.slice(0, 20),
    }, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify({
    ok: true,
    target_count: report.target_count,
    report_path: reportPath,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
