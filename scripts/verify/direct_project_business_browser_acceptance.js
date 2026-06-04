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

const SOURCE_DOCUMENT = 'user:direct_project_business_menu:2026-05-30';
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:18081';
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const BROWSER_EXECUTABLE_PATH = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\..+$/, '');
const OUT_DIR = path.join(ARTIFACTS_DIR, 'browser', 'direct-project-business', ts);

const SCREENSHOT_NAMES = new Set([
  '报价单',
  '零星用工',
  '机械台班记录',
  '管理人员工资表',
  '油卡登记',
  '工程结算单',
]);

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
    '# Direct Project Business Browser Acceptance',
    '',
    `- ok: ${report.ok}`,
    `- frontend_url: ${report.frontend_url}`,
    `- db_name: ${report.db_name}`,
    `- source_document: ${report.source_document}`,
    `- checked_count: ${report.summary.checked_count}`,
    `- pass_count: ${report.summary.pass_count}`,
    `- fail_count: ${report.summary.fail_count}`,
    `- fatal_console_error_count: ${report.summary.fatal_console_error_count}`,
    '',
    '| seq | group | menu | action | visible rows | status | screenshot |',
    '| ---: | --- | --- | ---: | ---: | --- | --- |',
  ];
  for (const row of report.rows) {
    lines.push(
      `| ${row.priority_sequence} | ${row.group} | ${row.name} | ${row.action_id} | ${row.row_count} | ${row.status} | ${row.screenshot || ''} |`,
    );
  }
  fs.writeFileSync(path.join(OUT_DIR, 'report.md'), lines.join('\n') + '\n', 'utf8');
}

function meaningfulConsoleErrors(messages) {
  return messages.filter((message) => {
    const text = normalize(message);
    if (!text) return false;
    if (/favicon\.ico/.test(text)) return false;
    if (/Failed to load resource: the server responded with a status of 404/.test(text)) return false;
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
        'X-Trace-Id': `direct-project-browser-${Date.now()}`,
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
    domain: [['source_document', '=', SOURCE_DOCUMENT]],
    fields: [
      'priority_sequence',
      'legacy_menu_group',
      'legacy_menu_name',
      'target_action_id',
      'target_model',
      'surface_contract_status',
    ],
    order: 'priority_sequence',
    limit: 80,
    context: { active_test: false },
  });
  return (Array.isArray(data.records) ? data.records : [])
    .map((row) => {
      const action = row.target_action_id;
      return {
        priority_sequence: Number(row.priority_sequence || 0),
        group: normalize(row.legacy_menu_group),
        name: normalize(row.legacy_menu_name),
        model: normalize(row.target_model),
        action_id: Array.isArray(action) ? Number(action[0] || 0) : Number(action || 0),
        surface_contract_status: normalize(row.surface_contract_status),
      };
    })
    .filter((row) => row.action_id > 0 && row.model);
}

async function waitForList(page) {
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    if (/页面加载失败|页面渲染失败|System exception|NAV_MENU_NO_ACTION/.test(text)) return true;
    if (/没有匹配记录|暂无数据|0 条/.test(text)) return true;
    return Boolean(document.querySelector('table.flat-table tbody tr, table.group-table tbody tr, .table table tbody tr, table tbody tr'));
  }, null, { timeout: 45000 });
  const bodyText = normalize(await page.locator('body').innerText({ timeout: 5000 }).catch(() => ''));
  if (/页面加载失败|页面渲染失败|System exception|NAV_MENU_NO_ACTION/.test(bodyText)) {
    throw new Error(bodyText.slice(0, 500));
  }
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

async function bodyProbe(page) {
  return page.evaluate(() => {
    const text = String(document.body?.textContent || '').replace(/\s+/g, ' ').trim();
    const title = String(document.querySelector('h1,h2,.page-title,.action-title')?.textContent || '').replace(/\s+/g, ' ').trim();
    return { title, text: text.slice(0, 800) };
  });
}

async function run() {
  ensureDir(OUT_DIR);
  const launchOptions = { headless: true, args: ['--no-sandbox'] };
  if (BROWSER_EXECUTABLE_PATH) launchOptions.executablePath = BROWSER_EXECUTABLE_PATH;
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
    source_document: SOURCE_DOCUMENT,
    artifact_dir: OUT_DIR,
    rows: [],
    summary: { checked_count: 0, pass_count: 0, fail_count: 0, fatal_console_error_count: 0 },
  };

  try {
    await login(page);
    const rows = await fetchPlanRows(page);
    if (rows.length !== 34) throw new Error(`expected 34 direct-project plan rows, got ${rows.length}`);
    for (const plan of rows) {
      const row = {
        ...plan,
        url: `${FRONTEND_URL}/a/${plan.action_id}?db=${encodeURIComponent(DB_NAME)}&direct_project_acceptance=${Date.now()}`,
        row_count: 0,
        status: 'FAIL',
        errors: [],
        screenshot: '',
        body_probe: {},
      };
      try {
        await page.goto(row.url, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForLoadState('networkidle', { timeout: 45000 }).catch(() => undefined);
        await waitForList(page);
        row.row_count = await visibleRowCount(page);
        row.body_probe = await bodyProbe(page);
        if (row.row_count < 1) row.errors.push('no_visible_rows');
        if (SCREENSHOT_NAMES.has(plan.name)) {
          const fileName = `${String(plan.priority_sequence).padStart(3, '0')}_${plan.name.replace(/[^\w\u4e00-\u9fa5]+/g, '_')}.png`;
          await page.screenshot({ path: path.join(OUT_DIR, fileName), fullPage: true });
          row.screenshot = fileName;
        }
        row.status = row.errors.length ? 'FAIL' : 'PASS';
      } catch (err) {
        row.errors.push(err && err.message ? err.message : String(err));
        const fileName = `${String(plan.priority_sequence).padStart(3, '0')}_${plan.name.replace(/[^\w\u4e00-\u9fa5]+/g, '_')}_failure.png`;
        await page.screenshot({ path: path.join(OUT_DIR, fileName), fullPage: true }).catch(() => undefined);
        row.screenshot = fileName;
      }
      report.rows.push(row);
    }
    const fatalConsoleErrors = meaningfulConsoleErrors(consoleErrors);
    report.summary.checked_count = report.rows.length;
    report.summary.pass_count = report.rows.filter((row) => row.status === 'PASS').length;
    report.summary.fail_count = report.rows.filter((row) => row.status !== 'PASS').length;
    report.summary.fatal_console_error_count = fatalConsoleErrors.length;
    report.fatal_console_errors = fatalConsoleErrors;
    report.ok = report.summary.fail_count === 0 && fatalConsoleErrors.length === 0;
    writeJson('summary.json', report);
    writeMarkdown(report);
    if (!report.ok) {
      throw new Error(`direct project browser acceptance failed: fail_count=${report.summary.fail_count}, fatal_console_errors=${fatalConsoleErrors.length}`);
    }
    console.log(`[direct_project_business_browser_acceptance] PASS artifacts=${OUT_DIR}`);
  } catch (err) {
    report.ok = false;
    report.error = err && err.message ? err.message : String(err);
    writeJson('summary.json', report);
    writeMarkdown(report);
    console.error(`[direct_project_business_browser_acceptance] FAIL ${report.error}`);
    console.error(`[direct_project_business_browser_acceptance] artifacts=${OUT_DIR}`);
    process.exitCode = 1;
  } finally {
    await browser.close().catch(() => undefined);
  }
}

run();
