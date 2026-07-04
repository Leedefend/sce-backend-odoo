import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { launchChromium } from './playwright_runtime.mjs';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const baseUrl = process.env.BASE_URL || 'http://127.0.0.1:18081';
const dbName = process.env.DB_NAME || process.env.DB || 'sc_demo';
const loginName = process.env.E2E_LOGIN || process.env.LOGIN || 'wutao';
const password = process.env.E2E_PASSWORD || process.env.PASSWORD || '123456';
const coverageReportPath = path.resolve(
  repoRoot,
  process.env.BUSINESS_CONFIG_COVERAGE_REPORT_PATH || 'artifacts/backend/business_config_coverage_gate.json',
);
const artifactRoot = path.resolve(
  repoRoot,
  process.env.BUSINESS_CONFIG_BROWSER_ARTIFACT_ROOT || 'artifacts/playwright/business-config-runtime-routes',
);
const reportPath = path.join(artifactRoot, 'report.json');
const maxRoutes = Number(process.env.BUSINESS_CONFIG_BROWSER_ROUTE_LIMIT || 60);
const analysisViewTypes = new Set(['pivot', 'graph', 'calendar', 'dashboard']);

function slug(value) {
  return String(value || '')
    .replace(/[^a-zA-Z0-9\u4e00-\u9fa5._-]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 120) || 'route';
}

function routeToUrl(route) {
  const text = String(route || '').trim();
  if (!text) return '';
  const url = new URL(text.startsWith('http') ? text : `${baseUrl}${text}`);
  url.searchParams.set('db', dbName);
  return url.toString();
}

function sampleViewType(sample) {
  const viewType = String(sample?.view_type || '').trim().toLowerCase();
  if (viewType) return viewType;
  const targets = Array.isArray(sample?.target_view_types) ? sample.target_view_types : [];
  return targets.map((item) => String(item || '').trim().toLowerCase()).find((item) => item) || '';
}

function runtimeRouteForSample(sample) {
  const route = String(sample?.runtime_route || '').trim();
  const viewType = sampleViewType(sample);
  if (!route || !analysisViewTypes.has(viewType)) return route;
  const url = new URL(route.startsWith('http') ? route : `${baseUrl}${route}`);
  url.searchParams.set('view_mode', viewType);
  return `${url.pathname}${url.search}`;
}

function collectSamples(report) {
  const rows = [];
  const seen = new Set();
  for (const scope of report?.scopes || []) {
    for (const sample of scope?.runtime_route_samples || []) {
      const route = runtimeRouteForSample(sample);
      const viewType = sampleViewType(sample);
      const seenKey = `${route}|${viewType}`;
      if (!route || seen.has(seenKey)) continue;
      seen.add(seenKey);
      rows.push({
        scope: String(scope?.scope || ''),
        action_id: Number(sample?.action_id || 0),
        name: String(sample?.name || ''),
        model: String(sample?.model || ''),
        severity: String(sample?.severity || ''),
        view_mode: String(sample?.view_mode || ''),
        view_type: viewType,
        target_view_types: Array.isArray(sample?.target_view_types) ? sample.target_view_types : [],
        sample_reason: String(sample?.sample_reason || ''),
        runtime_route: route,
      });
      if (maxRoutes > 0 && rows.length >= maxRoutes) return rows;
    }
  }
  return rows;
}

function isIgnorableConsoleError(text) {
  const value = String(text || '');
  return /^Failed to load resource: the server responded with a status of (403|404) /i.test(value);
}

async function login(page) {
  await page.goto(`${baseUrl}/login?db=${encodeURIComponent(dbName)}`, {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  });
  await page.locator('input').nth(0).fill(loginName);
  await page.locator('input[type="password"]').fill(password);
  if (await page.locator('input').count() >= 3) {
    const dbInput = page.locator('input').nth(2);
    if (await dbInput.isEnabled().catch(() => false)) {
      await dbInput.fill(dbName);
    }
  }
  await page.locator('button[type="submit"]').click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 60000 });
}

async function validateRoute(page, sample, index) {
  const startedAt = Date.now();
  const url = routeToUrl(sample.runtime_route);
  const screenshotPath = path.join(
    artifactRoot,
    `${String(index + 1).padStart(3, '0')}_${slug(sample.scope)}_${slug(sample.name || sample.model || sample.action_id)}.png`,
  );
  const row = {
    ...sample,
    url,
    screenshotPath,
    ok: false,
    elapsed_ms: 0,
    title: '',
    table_header_count: 0,
    row_count: 0,
    form_input_count: 0,
    failures: [],
  };
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(700);
    const bodyText = await page.locator('body').innerText({ timeout: 15000 }).catch(() => '');
    const title = await page.locator('h1, .page-title, .form-title').first().textContent({ timeout: 3000 }).catch(() => '');
    const tableHeaderCount = await page.locator('thead th').count().catch(() => 0);
    const rowCount = await page.locator('tbody tr').count().catch(() => 0);
    const formInputCount = await page.locator('input, textarea, select').count().catch(() => 0);
    const advancedViewCount = await page.locator('.advanced-view').count().catch(() => 0);
    const advancedItemCount = await page.locator('.advanced-item').count().catch(() => 0);
    const failures = [];
    if (page.url().includes('/login')) failures.push('redirected to login');
    if (!bodyText.trim()) failures.push('empty body');
    if (/Request failed|BAD_REQUEST|order 无效|页面加载失败|加载失败|发生错误|Traceback|Cannot read/i.test(bodyText)) {
      failures.push('visible runtime error');
    }
    if (!tableHeaderCount && !formInputCount && !rowCount && !advancedViewCount) {
      failures.push('no list, form, or advanced content detected');
    }
    if (analysisViewTypes.has(sample.view_type) && !advancedViewCount) {
      failures.push('analysis runtime did not render advanced view');
    }
    await page.screenshot({ path: screenshotPath, fullPage: true });
    return {
      ...row,
      ok: failures.length === 0,
      elapsed_ms: Date.now() - startedAt,
      title: String(title || '').trim(),
      table_header_count: tableHeaderCount,
      row_count: rowCount,
      form_input_count: formInputCount,
      advanced_view_count: advancedViewCount,
      advanced_item_count: advancedItemCount,
      failures,
    };
  } catch (err) {
    return {
      ...row,
      elapsed_ms: Date.now() - startedAt,
      failures: [err instanceof Error ? err.message : String(err)],
    };
  }
}

async function main() {
  await fs.mkdir(artifactRoot, { recursive: true });
  const coverageReport = JSON.parse(await fs.readFile(coverageReportPath, 'utf8'));
  const samples = collectSamples(coverageReport);
  if (!samples.length) {
    throw new Error(`coverage report has no runtime_route_samples: ${coverageReportPath}`);
  }

  const browser = await launchChromium({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: 'zh-CN' });
  const consoleErrors = [];
  const failedResponses = [];
  let currentRoute = '';
  page.on('console', (msg) => {
    const text = msg.text();
    if (msg.type() === 'error' && !isIgnorableConsoleError(text)) {
      consoleErrors.push({ route: currentRoute, text: text.slice(0, 500) });
    }
  });
  page.on('pageerror', (err) => consoleErrors.push({ route: currentRoute, text: err.message.slice(0, 500) }));
  page.on('response', (response) => {
    const status = response.status();
    if (status < 500) return;
    failedResponses.push({
      route: currentRoute,
      status,
      url: response.url(),
      method: response.request().method(),
      resource_type: response.request().resourceType(),
    });
  });

  await login(page);
  const results = [];
  for (let index = 0; index < samples.length; index += 1) {
    currentRoute = samples[index].runtime_route;
    const result = await validateRoute(page, samples[index], index);
    results.push(result);
    if ((index + 1) % 10 === 0 || index === samples.length - 1) {
      console.log(`[business_config_browser] ${index + 1}/${samples.length} failed=${results.filter((item) => !item.ok).length}`);
    }
  }
  await browser.close();

  const failures = results.filter((item) => !item.ok);
  const analysisRouteCount = results.filter((item) => analysisViewTypes.has(item.view_type)).length;
  if (!analysisRouteCount) {
    failures.push({
      ok: false,
      failures: ['no analysis runtime route sampled'],
      runtime_route: '',
      view_type: 'analysis',
    });
  }
  const report = {
    ok: failures.length === 0 && consoleErrors.length === 0 && failedResponses.length === 0,
    base_url: baseUrl,
    db_name: dbName,
    login: loginName,
    coverage_report_path: coverageReportPath,
    route_count: samples.length,
    analysis_route_count: analysisRouteCount,
    failure_count: failures.length,
    console_error_count: consoleErrors.length,
    failed_response_count: failedResponses.length,
    failures,
    console_errors: consoleErrors,
    failed_responses: failedResponses,
    results,
  };
  await fs.writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  if (!report.ok) {
    console.error(JSON.stringify({ ...report, results: results.slice(0, 20) }, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify({
    ok: true,
    route_count: samples.length,
    report_path: reportPath,
  }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
