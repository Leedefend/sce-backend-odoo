#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const ROOT = path.resolve(__dirname, '..', '..');
const MANIFEST = path.join(ROOT, 'docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json');
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://1.95.85.92:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.join(ROOT, 'artifacts');
const OUT_DIR = process.env.SCBS55_BROWSER_FIELD_OUT || path.join(
  ARTIFACTS_DIR,
  'migration',
  'scbs55_user_acceptance_browser_field_guard_v1',
);
const BROWSER_EXECUTABLE_PATH = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '';
const HELPER_HEADERS = new Set(['', '序号', '列', '操作', 'Actions']);

const requireBase = fs.existsSync(path.join(ROOT, 'frontend/apps/web/package.json'))
  ? path.join(ROOT, 'frontend/apps/web/package.json')
  : path.join(ROOT, 'package.json');
const requireFromRoot = createRequire(requireBase);
const { chromium } = requireFromRoot('playwright');

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, payload) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, JSON.stringify(payload, null, 2) + '\n', 'utf8');
}

function safeName(value) {
  return normalize(value).replace(/[^\w\u4e00-\u9fa5]+/g, '_').replace(/^_+|_+$/g, '') || 'surface';
}

function meaningfulConsoleErrors(messages) {
  return messages.filter((message) => {
    const text = normalize(message);
    if (!text) return false;
    if (/Failed to load resource: the server responded with a status of 404/.test(text)) return false;
    if (/favicon\.ico/.test(text)) return false;
    return true;
  });
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}&t=${Date.now()}`, {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await page.locator('input[type="password"]').fill(PASSWORD);
  if (await inputs.count() >= 3) {
    const dbInput = inputs.nth(2);
    if (await dbInput.isEditable().catch(() => false)) {
      await dbInput.fill(DB_NAME);
    }
  }
  const submit = page.locator('button[type="submit"], button').filter({ hasText: /^登录$/ }).first();
  await submit.click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 60000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);
}

async function waitForList(page) {
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    if (/页面加载失败|页面渲染失败|System exception|NAV_MENU_NO_ACTION|Traceback|contract not renderable/i.test(text)) return true;
    if (/没有匹配记录|暂无数据|0\s*条/.test(text)) return true;
    return Boolean(document.querySelector('table.flat-table thead, table.group-table thead, .table table thead, table thead'));
  }, null, { timeout: 60000 });
  const bodyText = normalize(await page.locator('body').innerText({ timeout: 10000 }).catch(() => ''));
  if (/页面加载失败|页面渲染失败|System exception|NAV_MENU_NO_ACTION|Traceback|contract not renderable/i.test(bodyText)) {
    throw new Error(bodyText.slice(0, 500));
  }
}

async function readVisibleTable(page) {
  return page.evaluate((helperHeadersList) => {
    const helperHeaders = new Set(helperHeadersList);
    function normalizeText(value) {
      return String(value || '').replace(/\s+/g, ' ').trim();
    }
    function visibleTable(table) {
      const rect = table.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    }
    function headerText(node) {
      const clone = node.cloneNode(true);
      for (const child of Array.from(clone.querySelectorAll('svg,.sort-indicator,.column-resize-handle,[aria-hidden="true"]'))) {
        child.remove();
      }
      return normalizeText(clone.textContent);
    }
    const tables = Array.from(document.querySelectorAll('table.flat-table, table.group-table, .table table, table'))
      .filter(visibleTable)
      .map((table) => {
        const headers = Array.from(table.querySelectorAll('thead th'))
          .map(headerText)
          .filter((item) => !helperHeaders.has(item));
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        const firstRow = rows[0]
          ? Array.from(rows[0].querySelectorAll('td'))
            .filter((cell) => !cell.classList.contains('cell-select')
              && !cell.classList.contains('cell-row-number')
              && !cell.classList.contains('cell-column-picker'))
            .map((cell) => normalizeText(cell.textContent))
          : [];
        return { headers, visibleRowCount: rows.length, firstRow };
      });
    tables.sort((left, right) => {
      if (right.headers.length !== left.headers.length) return right.headers.length - left.headers.length;
      return right.visibleRowCount - left.visibleRowCount;
    });
    const bodyText = normalizeText(document.body?.textContent || '');
    const totalMatches = Array.from(bodyText.matchAll(/共\s*([0-9,]+)\s*(?:条|项|记录)?/g))
      .map((match) => Number(String(match[1] || '').replace(/,/g, '')))
      .filter((value) => Number.isFinite(value));
    return {
      table: tables[0] || { headers: [], visibleRowCount: 0, firstRow: [] },
      total: totalMatches.length ? Math.max(...totalMatches) : null,
      bodySample: bodyText.slice(0, 1000),
    };
  }, Array.from(HELPER_HEADERS));
}

function compareHeaders(actualHeaders, expectedHeaders) {
  const actual = actualHeaders.slice(0, expectedHeaders.length);
  const missing = [];
  for (let index = 0; index < expectedHeaders.length; index += 1) {
    if (actual[index] !== expectedHeaders[index]) {
      missing.push({ index, expected: expectedHeaders[index], actual: actual[index] || '' });
    }
  }
  const extra = actualHeaders.slice(expectedHeaders.length).filter((item) => !HELPER_HEADERS.has(item));
  return { missing, extra };
}

async function run() {
  ensureDir(OUT_DIR);
  const manifest = readJson(MANIFEST);
  const launchOptions = { headless: true, args: ['--no-sandbox'] };
  if (BROWSER_EXECUTABLE_PATH) launchOptions.executablePath = BROWSER_EXECUTABLE_PATH;
  const browser = await chromium.launch(launchOptions);
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 }, locale: 'zh-CN' });
  const consoleErrors = [];
  const apiDataCalls = [];
  let currentSurface = '';

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push({ surface: currentSurface, text: msg.text() });
  });
  page.on('pageerror', (err) => consoleErrors.push({ surface: currentSurface, text: err.message }));
  page.on('response', async (response) => {
    if (!response.url().includes('/api/v1/intent')) return;
    let requestPayload = {};
    try {
      requestPayload = JSON.parse(response.request().postData() || '{}');
    } catch {
      requestPayload = {};
    }
    if (requestPayload.intent !== 'api.data') return;
    const params = requestPayload.params || {};
    let body = {};
    try {
      body = await response.json();
    } catch {
      body = {};
    }
    const data = body && typeof body === 'object' && body.data ? body.data : body;
    const records = Array.isArray(data.records) ? data.records : Array.isArray(data.rows) ? data.rows : [];
    const fields = Array.isArray(params.fields) ? params.fields.map(String) : [];
    const recordKeys = [...new Set(records.flatMap((row) => Object.keys(row || {})))];
    apiDataCalls.push({
      surface: currentSurface,
      ok: response.ok() && body.ok !== false,
      status: response.status(),
      model: normalize(params.model),
      op: normalize(params.op),
      requestedFieldCount: fields.length,
      recordCount: records.length,
      missingRequestedFields: records.length ? fields.filter((field) => field !== 'id' && !recordKeys.includes(field)) : [],
      error: body.error || body.message || '',
    });
  });

  const report = {
    ok: false,
    frontend_url: FRONTEND_URL,
    db_name: DB_NAME,
    login: LOGIN,
    manifest: path.relative(ROOT, MANIFEST),
    artifact_dir: OUT_DIR,
    rows: [],
    console_errors: consoleErrors,
    api_data_calls: apiDataCalls,
    summary: {},
  };

  try {
    await login(page);
    for (const surface of manifest.surfaces || []) {
      currentSurface = surface.key;
      const expectedHeaders = (surface.new.expected_headers || []).map(normalize);
      const row = {
        key: surface.key,
        name: surface.name,
        menu_id: surface.new.menu_id,
        action_id: surface.new.action_id,
        expected_count: surface.new.expected_count,
        expected_headers: expectedHeaders,
        actual_total: null,
        actual_headers: [],
        first_row_values: [],
        visible_row_count: 0,
        url: '',
        screenshot: '',
        status: 'FAIL',
        errors: [],
      };
      const candidates = [
        `${FRONTEND_URL}/m/${surface.new.menu_id}?db=${encodeURIComponent(DB_NAME)}&scbs55_field_guard=${Date.now()}`,
        `${FRONTEND_URL}/a/${surface.new.action_id}?db=${encodeURIComponent(DB_NAME)}&menu_id=${surface.new.menu_id}&scbs55_field_guard=${Date.now()}`,
      ];
      for (const url of candidates) {
        try {
          row.url = url;
          await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
          await page.waitForLoadState('networkidle', { timeout: 45000 }).catch(() => undefined);
          await waitForList(page);
          const visible = await readVisibleTable(page);
          row.actual_total = visible.total;
          row.actual_headers = visible.table.headers;
          row.first_row_values = visible.table.firstRow;
          row.visible_row_count = visible.table.visibleRowCount;
          const headerDiff = compareHeaders(row.actual_headers, expectedHeaders);
          if (row.actual_total !== Number(row.expected_count)) {
            row.errors.push(`total_mismatch:${row.actual_total}!=${row.expected_count}`);
          }
          if (headerDiff.missing.length) row.errors.push(`header_order_mismatch:${JSON.stringify(headerDiff.missing)}`);
          if (headerDiff.extra.length) row.errors.push(`extra_headers:${headerDiff.extra.join(',')}`);
          if (row.visible_row_count < 1 && Number(row.expected_count) > 0) row.errors.push('no_rows_rendered');
          if (!row.first_row_values.some((value) => normalize(value))) row.errors.push('first_row_has_no_visible_data');
          row.status = row.errors.length ? 'FAIL' : 'PASS';
          break;
        } catch (err) {
          row.errors.push(err && err.message ? err.message : String(err));
        }
      }
      const screenshot = `${safeName(surface.key)}_${safeName(surface.name)}.png`;
      await page.screenshot({ path: path.join(OUT_DIR, screenshot), fullPage: true }).catch(() => undefined);
      row.screenshot = screenshot;
      report.rows.push(row);
    }

    const fatalConsoleErrors = meaningfulConsoleErrors(consoleErrors.map((item) => item.text));
    const dataFieldFailures = apiDataCalls.filter((call) => !call.ok || call.missingRequestedFields.length);
    report.summary = {
      checked_count: report.rows.length,
      pass_count: report.rows.filter((row) => row.status === 'PASS').length,
      fail_count: report.rows.filter((row) => row.status !== 'PASS').length,
      console_error_count: consoleErrors.length,
      fatal_console_error_count: fatalConsoleErrors.length,
      api_data_call_count: apiDataCalls.length,
      api_data_field_failure_count: dataFieldFailures.length,
    };
    report.fatal_console_errors = fatalConsoleErrors;
    report.api_data_field_failures = dataFieldFailures;
    report.ok = report.summary.fail_count === 0 && fatalConsoleErrors.length === 0 && dataFieldFailures.length === 0;
    writeJson(path.join(OUT_DIR, 'summary.json'), report);
    if (!report.ok) {
      throw new Error(`browser field guard failed: fail_count=${report.summary.fail_count}, console=${fatalConsoleErrors.length}, api_data=${dataFieldFailures.length}`);
    }
    console.log(`[scbs55-browser-field-guard] PASS artifacts=${OUT_DIR}`);
  } catch (err) {
    report.ok = false;
    report.error = err && err.message ? err.message : String(err);
    writeJson(path.join(OUT_DIR, 'summary.json'), report);
    console.error(`[scbs55-browser-field-guard] FAIL ${report.error}`);
    console.error(`[scbs55-browser-field-guard] artifacts=${OUT_DIR}`);
    process.exitCode = 1;
  } finally {
    await browser.close().catch(() => undefined);
  }
}

run();
