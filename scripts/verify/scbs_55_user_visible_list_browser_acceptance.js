#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const requireBase = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? path.join(process.cwd(), 'frontend/apps/web/package.json')
  : path.join(process.cwd(), 'package.json');
const requireFromRoot = createRequire(requireBase);
const { chromium } = requireFromRoot('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5174';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const BROWSER_EXECUTABLE_PATH = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '';
const OUT_DIR = path.join(
  ARTIFACTS_DIR,
  'browser',
  'scbs55-user-visible-list',
  new Date().toISOString().replace(/[-:]/g, '').replace(/\..+$/, ''),
);

const SCREENSHOT_SEQS = new Set([350, 360, 410]);
const ALLOW_ZERO_RECORD_SEQS = new Set([130]);
const HELPER_HEADERS = new Set(['', '序号', '列', '操作', 'Actions']);

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function writeJson(name, payload) {
  ensureDir(OUT_DIR);
  fs.writeFileSync(path.join(OUT_DIR, name), JSON.stringify(payload, null, 2) + '\n', 'utf8');
}

function writeMarkdown(report) {
  const lines = [
    '# SCBS55 User Visible List Browser Acceptance',
    '',
    `- ok: ${report.ok}`,
    `- frontend_url: ${report.frontend_url}`,
    `- db_name: ${report.db_name}`,
    `- login: ${report.login}`,
    `- checked_count: ${report.summary.checked_count}`,
    `- pass_count: ${report.summary.pass_count}`,
    `- fail_count: ${report.summary.fail_count}`,
    '',
    '| seq | menu | action | rows | headers | status | screenshot |',
    '| ---: | --- | ---: | ---: | ---: | --- | --- |',
  ];
  for (const row of report.rows) {
    lines.push(
      `| ${row.seq} | ${row.name} | ${row.action_id} | ${row.row_count} | ${row.actual_headers.length} | ${row.status} | ${row.screenshot || ''} |`,
    );
  }
  fs.writeFileSync(path.join(OUT_DIR, 'report.md'), lines.join('\n') + '\n', 'utf8');
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
    waitUntil: 'networkidle',
    timeout: 45000,
  });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  const dbInput = inputs.nth(2);
  if (await dbInput.isEditable().catch(() => false)) {
    await dbInput.fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);
}

async function authToken(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intent(page, intentName, params) {
  const token = await authToken(page);
  return page.evaluate(async ({ dbName, tokenValue, intentName, params }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: tokenValue ? `Bearer ${tokenValue}` : '',
        'X-Trace-Id': `scbs55-list-browser-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || body.ok === false) {
      throw new Error(body?.error?.message || body?.message || `${intentName} failed`);
    }
    return body.data || {};
  }, { dbName: DB_NAME, tokenValue: token, intentName, params });
}

async function fetchPlanRows(page) {
  const data = await intent(page, 'api.data', {
    op: 'list',
    model: 'sc.legacy.user.priority.menu.plan',
    domain: [
      ['source_document', '=', '/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx'],
      ['list_field_contract', '!=', false],
    ],
    fields: [
      'priority_sequence',
      'legacy_menu_group',
      'legacy_menu_name',
      'target_action_id',
      'target_model',
      'list_field_contract',
    ],
    order: 'priority_sequence',
    limit: 80,
    context: { active_test: false },
  });
  const records = Array.isArray(data.records) ? data.records : [];
  return records
    .map((row) => {
      const actionValue = row.target_action_id;
      const actionId = Array.isArray(actionValue) ? Number(actionValue[0] || 0) : Number(actionValue || 0);
      const contract = Array.isArray(row.list_field_contract) ? row.list_field_contract : [];
      const seenLabels = new Set();
      const labels = contract
        .map((item) => (item && typeof item === 'object' ? normalize(item.legacy_label) : ''))
        .filter((label) => {
          if (!label || label === '操作') return false;
          if (seenLabels.has(label)) return false;
          seenLabels.add(label);
          return true;
        });
      return {
        seq: Number(row.priority_sequence || 0),
        group: normalize(row.legacy_menu_group),
        name: normalize(row.legacy_menu_name),
        model: normalize(row.target_model),
        action_id: actionId,
        expected_headers: labels,
      };
    })
    .filter((row) => row.action_id > 0 && row.expected_headers.length > 0);
}

async function waitForList(page) {
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    if (/页面加载失败|页面渲染失败|System exception|NAV_MENU_NO_ACTION/.test(text)) return true;
    if (/没有匹配记录|暂无数据|0 条/.test(text)) return true;
    return Boolean(document.querySelector('table.flat-table thead, table.group-table thead, .table table thead, table thead'));
  }, null, { timeout: 45000 });
  const bodyText = normalize(await page.locator('body').innerText({ timeout: 5000 }).catch(() => ''));
  if (/页面加载失败|页面渲染失败|System exception|NAV_MENU_NO_ACTION/.test(bodyText)) {
    throw new Error(bodyText.slice(0, 400));
  }
}

async function tableHeaders(page) {
  return page.evaluate((helperHeaders) => {
    function normalizeText(value) {
      return String(value || '').replace(/\s+/g, ' ').trim();
    }

    function headerText(node) {
      const clone = node.cloneNode(true);
      for (const child of Array.from(clone.querySelectorAll('svg,.sort-indicator,.column-resize-handle,[aria-hidden="true"]'))) {
        child.remove();
      }
      return normalizeText(clone.textContent);
    }

    const tables = Array.from(document.querySelectorAll('table.flat-table, table.group-table, .table table, table'));
    const candidates = tables
      .filter((table) => {
        const rect = table.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      })
      .map((table) => Array.from(table.querySelectorAll('thead th'))
        .map(headerText)
        .filter((text) => !helperHeaders.includes(text)));
    candidates.sort((left, right) => right.length - left.length);
    return candidates[0] || [];
  }, Array.from(HELPER_HEADERS));
}

async function firstRowValues(page) {
  return page.evaluate(() => {
    function normalizeText(value) {
      return String(value || '').replace(/\s+/g, ' ').trim();
    }

    const tables = Array.from(document.querySelectorAll('table.flat-table, table.group-table, .table table, table'))
      .filter((table) => {
        const rect = table.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      });
    const candidates = tables.map((table) => {
      const row = table.querySelector('tbody tr');
      if (!row) return [];
      return Array.from(row.querySelectorAll('td'))
        .filter((cell) => !cell.classList.contains('cell-select')
          && !cell.classList.contains('cell-row-number')
          && !cell.classList.contains('cell-column-picker'))
        .map((cell) => normalizeText(cell.textContent));
    });
    candidates.sort((left, right) => right.length - left.length);
    return candidates[0] || [];
  });
}

async function visibleRowCount(page) {
  return page.evaluate(() => {
    const tables = Array.from(document.querySelectorAll('table.flat-table, table.group-table, .table table, table'))
      .filter((table) => {
        const rect = table.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      });
    return tables.reduce((count, table) => count + table.querySelectorAll('tbody tr').length, 0);
  });
}

async function run() {
  ensureDir(OUT_DIR);
  const launchOptions = { headless: true, args: ['--no-sandbox'] };
  if (BROWSER_EXECUTABLE_PATH) {
    launchOptions.executablePath = BROWSER_EXECUTABLE_PATH;
  }
  const browser = await chromium.launch(launchOptions);
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 }, locale: 'zh-CN' });
  const consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => consoleErrors.push(err.message));

  const report = {
    ok: false,
    frontend_url: FRONTEND_URL,
    db_name: DB_NAME,
    login: LOGIN,
    artifact_dir: OUT_DIR,
    rows: [],
    console_errors: consoleErrors,
    summary: { checked_count: 0, pass_count: 0, fail_count: 0 },
  };

  try {
    await login(page);
    const planRows = await fetchPlanRows(page);
    if (!planRows.length) throw new Error('no user-visible list plan rows resolved through browser intent');

    for (const plan of planRows) {
      const actionUrl = `${FRONTEND_URL}/a/${plan.action_id}?db=${encodeURIComponent(DB_NAME)}&scbs55_browser_acceptance=${Date.now()}`;
      const row = {
        ...plan,
        url: actionUrl,
        actual_headers: [],
        first_row_values: [],
        row_count: 0,
        status: 'FAIL',
        errors: [],
        notes: [],
        screenshot: '',
      };
      try {
        await page.goto(actionUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForLoadState('networkidle', { timeout: 45000 }).catch(() => undefined);
        await waitForList(page);
        row.actual_headers = await tableHeaders(page);
        row.first_row_values = await firstRowValues(page);
        row.row_count = await visibleRowCount(page);
        if (row.row_count < 1 && ALLOW_ZERO_RECORD_SEQS.has(plan.seq)) {
          row.status = 'PASS';
          row.notes.push('zero_record_allowed');
          if (SCREENSHOT_SEQS.has(plan.seq)) {
            const fileName = `seq_${String(plan.seq).padStart(3, '0')}_${plan.name.replace(/[^\w\u4e00-\u9fa5]+/g, '_')}.png`;
            await page.screenshot({ path: path.join(OUT_DIR, fileName), fullPage: true });
            row.screenshot = fileName;
          }
          report.rows.push(row);
          continue;
        }
        const visibleHeaders = row.actual_headers.slice(0, plan.expected_headers.length);
        const extraHeaders = row.actual_headers.slice(plan.expected_headers.length);
        const missing = plan.expected_headers.filter((header, idx) => visibleHeaders[idx] !== header);
        const extraMeaningful = extraHeaders.filter((header) => !['操作', 'Actions'].includes(header));
        if (missing.length) row.errors.push(`header_order_mismatch:${missing.join(',')}`);
        if (extraMeaningful.length) row.errors.push(`extra_headers:${extraMeaningful.join(',')}`);
        if (row.row_count < 1 && plan.seq !== 130) row.errors.push('no_rows_rendered');
        if (SCREENSHOT_SEQS.has(plan.seq)) {
          const fileName = `seq_${String(plan.seq).padStart(3, '0')}_${plan.name.replace(/[^\w\u4e00-\u9fa5]+/g, '_')}.png`;
          await page.screenshot({ path: path.join(OUT_DIR, fileName), fullPage: true });
          row.screenshot = fileName;
        }
        row.status = row.errors.length ? 'FAIL' : 'PASS';
      } catch (err) {
        row.errors.push(err && err.message ? err.message : String(err));
        const fileName = `seq_${String(plan.seq).padStart(3, '0')}_failure.png`;
        await page.screenshot({ path: path.join(OUT_DIR, fileName), fullPage: true }).catch(() => undefined);
        row.screenshot = fileName;
      }
      report.rows.push(row);
    }

    report.summary.checked_count = report.rows.length;
    report.summary.pass_count = report.rows.filter((row) => row.status === 'PASS').length;
    report.summary.fail_count = report.rows.filter((row) => row.status !== 'PASS').length;
    const fatalConsoleErrors = meaningfulConsoleErrors(consoleErrors);
    report.summary.console_error_count = consoleErrors.length;
    report.summary.fatal_console_error_count = fatalConsoleErrors.length;
    report.fatal_console_errors = fatalConsoleErrors;
    report.ok = report.summary.fail_count === 0 && fatalConsoleErrors.length === 0;
    writeJson('summary.json', report);
    writeMarkdown(report);
    if (!report.ok) {
      throw new Error(`browser acceptance failed: fail_count=${report.summary.fail_count}, fatal_console_errors=${fatalConsoleErrors.length}`);
    }
    console.log(`[scbs55_list_browser_acceptance] PASS artifacts=${OUT_DIR}`);
  } catch (err) {
    report.ok = false;
    report.error = err && err.message ? err.message : String(err);
    writeJson('summary.json', report);
    writeMarkdown(report);
    console.error(`[scbs55_list_browser_acceptance] FAIL ${report.error}`);
    console.error(`[scbs55_list_browser_acceptance] artifacts=${OUT_DIR}`);
    process.exitCode = 1;
  } finally {
    await browser.close().catch(() => undefined);
  }
}

run();
