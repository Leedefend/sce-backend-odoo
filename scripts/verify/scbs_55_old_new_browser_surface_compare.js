#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { createRequire } = require('module');

const requireBase = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? path.join(process.cwd(), 'frontend/apps/web/package.json')
  : path.join(process.cwd(), 'package.json');
const requireFromRoot = createRequire(requireBase);
const { chromium } = requireFromRoot('playwright');
const { requireOnlineCapture } = require('./online_capture_security');

const OLD_CAPTURE = requireOnlineCapture('scbs');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5174';
const DB_NAME = process.env.DB_NAME || 'sc_odoo';
const NEW_LOGIN = process.env.E2E_LOGIN || '';
const NEW_PASSWORD = process.env.E2E_PASSWORD || '';
const OLD_BASE_URL = OLD_CAPTURE.baseUrl;
const OLD_LOGIN = OLD_CAPTURE.username;
const OLD_PASSWORD = OLD_CAPTURE.password;
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const OUT_DIR = path.join(
  ARTIFACTS_DIR,
  'browser',
  'scbs55-old-new-surface-compare',
  new Date().toISOString().replace(/[-:]/g, '').replace(/\..+$/, ''),
);
const SOURCE_DOCUMENT = '/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx';
const ALLOW_ZERO_RECORD_SEQS = new Set([13, 130]);

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function md5(value) {
  return crypto.createHash('md5').update(value, 'utf8').digest('hex');
}

function splitItems(raw) {
  return String(raw || '').split(';').map((item) => item.trim()).filter(Boolean);
}

function itemLabel(raw) {
  const text = normalize(raw);
  return text.includes('(') ? text.split('(', 1)[0].trim() : text;
}

function visibleLabelsFromCsv(row) {
  return splitItems(row.visible_columns).map(itemLabel);
}

function configIdFromLink(link) {
  try {
    const parsed = new URL(link, OLD_BASE_URL + '/');
    return parsed.searchParams.get('ConfigId') || parsed.searchParams.get('configId') || '';
  } catch {
    return '';
  }
}

function visibleLabelsFromConfig(config) {
  const detail = JSON.parse(config.DETAIL_CONFIG || '{}');
  const columns = (((detail.ContentTable || {}).TableConfig || {}).ColumnConfig) || [];
  const labels = [];
  function visit(items) {
    for (const item of items || []) {
      const info = item.Info || {};
      if (info.IsHide === true) continue;
      const name = normalize(info.Name);
      if (name) labels.push(name);
      if (item.ChildConfig) visit(item.ChildConfig);
    }
  }
  visit(columns);
  return labels;
}

function readCsv(filePath) {
  const text = fs.readFileSync(filePath, 'utf8').replace(/^\uFEFF/, '');
  const lines = text.split(/\r?\n/).filter((line) => line.length);
  const headers = parseCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line);
    const row = {};
    headers.forEach((header, index) => {
      row[header] = values[index] || '';
    });
    return row;
  });
}

function parseCsvLine(line) {
  const out = [];
  let cur = '';
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (quoted) {
      if (ch === '"' && line[i + 1] === '"') {
        cur += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        cur += ch;
      }
    } else if (ch === ',') {
      out.push(cur);
      cur = '';
    } else if (ch === '"') {
      quoted = true;
    } else {
      cur += ch;
    }
  }
  out.push(cur);
  return out;
}

function writeJson(name, payload) {
  ensureDir(OUT_DIR);
  fs.writeFileSync(path.join(OUT_DIR, name), JSON.stringify(payload, null, 2) + '\n', 'utf8');
}

function writeMarkdown(report) {
  const lines = [
    '# SCBS55 Old/New Browser Surface Compare',
    '',
    `- status: ${report.status}`,
    `- old_user: ${report.old_user.UserName} / ${report.old_user.PersonName}`,
    `- new_user: ${report.new_user}`,
    `- frontend_url: ${report.frontend_url}`,
    `- db_name: ${report.db_name}`,
    `- row_count: ${report.row_count}`,
    `- failure_count: ${report.failure_count}`,
    '',
    '| seq | old name | new name | old visible | old fields | new opened | new rows | new fields | status |',
    '| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |',
  ];
  for (const row of report.rows) {
    lines.push(`| ${row.seq} | ${row.old_name} | ${row.new_name} | ${row.old_menu_visible} | ${row.old_field_match} | ${row.new_page_opened} | ${row.new_row_count} | ${row.new_field_match} | ${row.status} |`);
  }
  lines.push('', '## Failures', '', '```json', JSON.stringify(report.failures, null, 2), '```', '');
  fs.writeFileSync(path.join(OUT_DIR, 'report.md'), lines.join('\n'), 'utf8');
}

async function oldBrowserBaseline(browser, csvRows) {
  if (!OLD_LOGIN || !OLD_PASSWORD) throw new Error('OLD_SCBS_USERNAME and OLD_SCBS_PASSWORD are required');
  const context = await browser.newContext({ locale: 'zh-CN' });
  const page = await context.newPage();
  await page.goto(`${OLD_BASE_URL}/System/User/Login`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const loginResult = await page.evaluate(async ({ oldLogin, oldPassword, oldBaseUrl, passwordMd5 }) => {
    const response = await fetch(`${oldBaseUrl}/api/System/UserApi/Login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        Type: 'Common',
        Param: {
          UserName: oldLogin,
          IsEncrypt: false,
          Password: oldPassword,
          PasswordMd5: passwordMd5,
          VerificationCodeKey: '',
          VerificationCode: '',
          EncryptLockKey: '',
          PhoneNumber: '',
          SMSVerificationCodeKey: '',
          SMSVerificationCode: '',
        },
      }),
    });
    return response.json();
  }, { oldLogin: OLD_LOGIN, oldPassword: OLD_PASSWORD, oldBaseUrl: OLD_BASE_URL, passwordMd5: md5(OLD_PASSWORD) });
  if (String(loginResult.Code) !== '10000' || !loginResult.Data?.Token) {
    throw new Error(`old login failed: ${loginResult.Code} ${loginResult.Msg || ''}`);
  }
  const token = loginResult.Data.Token;
  const home = await page.evaluate(async ({ oldBaseUrl, tokenValue }) => {
    const response = await fetch(`${oldBaseUrl}/api/HomeApi/GetCommonHomeInfo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Token: tokenValue },
      body: JSON.stringify({}),
    });
    return response.json();
  }, { oldBaseUrl: OLD_BASE_URL, tokenValue: token });
  const menus = home.Data?.MenuInfoArr || [];
  const menusByConfig = new Map();
  for (const menu of menus) {
    const configId = configIdFromLink(menu.LINK_URL || '');
    if (!configId) continue;
    if (!menusByConfig.has(configId)) menusByConfig.set(configId, []);
    menusByConfig.get(configId).push(menu);
  }
  const rows = [];
  for (const csvRow of csvRows) {
    const configId = normalize(csvRow.config_id);
    const expectedLabels = visibleLabelsFromCsv(csvRow);
    let menuMatches = configId ? (menusByConfig.get(configId) || []) : [];
    if (!menuMatches.length) {
      menuMatches = menus.filter((menu) => [normalize(menu.MENU_NAME), normalize(menu.DEFAULT_NAME)].includes(normalize(csvRow.name)));
    }
    let actualLabels = [];
    let configFetched = false;
    if (configId && csvRow.config_type === 'List') {
      const body = await page.evaluate(async ({ oldBaseUrl, tokenValue, configIdValue }) => {
        const response = await fetch(`${oldBaseUrl}/api/LowCode/FormApi/GetConfigById?Id=${encodeURIComponent(configIdValue)}&LoadInitData=true`, {
          headers: { Token: tokenValue },
        });
        return response.json();
      }, { oldBaseUrl: OLD_BASE_URL, tokenValue: token, configIdValue: configId });
      if (String(body.Code) !== '10000') throw new Error(`old config failed: ${configId} ${body.Msg || ''}`);
      configFetched = true;
      actualLabels = visibleLabelsFromConfig(body.Data);
    }
    rows.push({
      seq: Number(csvRow.seq),
      name: normalize(csvRow.name),
      config_id: configId,
      menu_visible: menuMatches.length > 0,
      config_fetched: configFetched,
      expected_labels: expectedLabels,
      actual_labels: actualLabels,
      field_match: expectedLabels.length ? JSON.stringify(expectedLabels) === JSON.stringify(actualLabels) : true,
    });
  }
  await page.screenshot({ path: path.join(OUT_DIR, 'old_system_login_context.png'), fullPage: true }).catch(() => undefined);
  await context.close();
  return { user: loginResult.Data, rows };
}

async function newLogin(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}&t=${Date.now()}`, {
    waitUntil: 'networkidle',
    timeout: 45000,
  });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(NEW_LOGIN);
  await inputs.nth(1).fill(NEW_PASSWORD);
  if (await inputs.nth(2).isEditable().catch(() => false)) await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);
}

async function newIntent(page, intentName, params) {
  const token = await page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
  return page.evaluate(async ({ dbName, tokenValue, intentName, params }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: tokenValue ? `Bearer ${tokenValue}` : '',
        'X-Trace-Id': `scbs55-old-new-browser-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || body.ok === false) throw new Error(body?.error?.message || body?.message || `${intentName} failed`);
    return body.data || {};
  }, { dbName: DB_NAME, tokenValue: token, intentName, params });
}

async function newPlanRows(page) {
  const data = await newIntent(page, 'api.data', {
    op: 'list',
    model: 'sc.legacy.user.priority.menu.plan',
    domain: [['source_document', '=', SOURCE_DOCUMENT]],
    fields: ['priority_sequence', 'legacy_menu_name', 'target_action_id', 'target_model', 'list_field_contract'],
    order: 'priority_sequence',
    limit: 80,
    context: { active_test: false },
  });
  return (data.records || []).map((record) => {
    const actionValue = record.target_action_id;
    const actionId = Array.isArray(actionValue) ? Number(actionValue[0] || 0) : Number(actionValue || 0);
    const contract = Array.isArray(record.list_field_contract) ? record.list_field_contract : [];
    const labels = [];
    const seen = new Set();
    for (const item of contract) {
      const label = normalize(item?.legacy_label);
      if (!label || label === '操作' || seen.has(label)) continue;
      seen.add(label);
      labels.push(label);
    }
    const rawSeq = Number(record.priority_sequence || 0);
    return {
      seq: rawSeq >= 10 && rawSeq % 10 === 0 ? rawSeq / 10 : rawSeq,
      name: normalize(record.legacy_menu_name),
      model: normalize(record.target_model),
      action_id: actionId,
      expected_headers: labels,
    };
  });
}

async function tableHeaders(page) {
  return page.evaluate(() => {
    const helper = new Set(['', '序号', '列', '操作', 'Actions']);
    function text(node) {
      const clone = node.cloneNode(true);
      for (const child of Array.from(clone.querySelectorAll('svg,.sort-indicator,.column-resize-handle,[aria-hidden="true"]'))) child.remove();
      return String(clone.textContent || '').replace(/\s+/g, ' ').trim();
    }
    const tables = Array.from(document.querySelectorAll('table.flat-table, table.group-table, .table table, table'))
      .filter((table) => {
        const rect = table.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      });
    const candidates = tables.map((table) => Array.from(table.querySelectorAll('thead th')).map(text).filter((value) => !helper.has(value)));
    candidates.sort((a, b) => b.length - a.length);
    return candidates[0] || [];
  });
}

async function waitForSurface(page, requireTable) {
  await page.waitForFunction((requireTableArg) => {
    const text = String(document.body?.textContent || '');
    if (/页面加载失败|页面渲染失败|System exception|NAV_MENU_NO_ACTION|INTERNAL_ERROR/.test(text)) return true;
    if (/没有匹配记录|暂无数据|0 条/.test(text)) return true;
    if (document.querySelector('table.flat-table thead, table.group-table thead, .table table thead, table thead')) return true;
    return !requireTableArg && Boolean(document.querySelector('main, .page, #app'));
  }, requireTable, { timeout: 45000 });
  await page.waitForTimeout(500);
}

async function tableRowCount(page) {
  return page.evaluate(() => Array.from(document.querySelectorAll('table.flat-table, table.group-table, .table table, table'))
    .filter((table) => {
      const rect = table.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    })
    .reduce((total, table) => total + table.querySelectorAll('tbody tr').length, 0));
}

async function pageBodyFailure(page) {
  const text = normalize(await page.locator('body').innerText({ timeout: 5000 }).catch(() => ''));
  if (/页面加载失败|页面渲染失败|System exception|NAV_MENU_NO_ACTION|INTERNAL_ERROR/.test(text)) return text.slice(0, 500);
  return '';
}

async function newBrowserBaseline(browser) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 960 }, locale: 'zh-CN' });
  const page = await context.newPage();
  await newLogin(page);
  const plans = await newPlanRows(page);
  const rows = [];
  for (const plan of plans) {
    console.log(`[new-browser] seq=${plan.seq} name=${plan.name} action=${plan.action_id}`);
    const result = {
      ...plan,
      page_opened: false,
      row_count: 0,
      actual_headers: [],
      field_match: true,
      error: '',
    };
    try {
      if (!plan.action_id) throw new Error('missing target_action_id');
      await page.goto(`${FRONTEND_URL}/a/${plan.action_id}?db=${encodeURIComponent(DB_NAME)}&scbs55_old_new_compare=${Date.now()}`, {
        waitUntil: 'domcontentloaded',
        timeout: 20000,
      });
      await waitForSurface(page, plan.expected_headers.length > 0);
      const failure = await pageBodyFailure(page);
      if (failure) throw new Error(failure);
      result.page_opened = true;
      result.actual_headers = await tableHeaders(page);
      result.row_count = await tableRowCount(page);
      if (ALLOW_ZERO_RECORD_SEQS.has(plan.seq) && result.row_count < 1) {
        result.field_match = true;
      } else if (plan.expected_headers.length) {
        const actual = result.actual_headers.slice(0, plan.expected_headers.length);
        result.field_match = JSON.stringify(actual) === JSON.stringify(plan.expected_headers);
      }
      if (result.row_count < 1 && !ALLOW_ZERO_RECORD_SEQS.has(plan.seq)) {
        throw new Error('no rows rendered');
      }
    } catch (err) {
      result.error = err?.message || String(err);
      result.field_match = false;
      await page.screenshot({ path: path.join(OUT_DIR, `new_seq_${String(plan.seq).padStart(3, '0')}_failure.png`), fullPage: true }).catch(() => undefined);
    }
    rows.push(result);
  }
  await context.close();
  return rows;
}

async function main() {
  ensureDir(OUT_DIR);
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    const csvRows = readCsv(path.join(process.cwd(), 'docs/migration_alignment/scbs_55_user_visible_surface_live_alignment_v1.csv'));
    const oldResult = await oldBrowserBaseline(browser, csvRows);
    const newRows = await newBrowserBaseline(browser);
    const oldBySeq = new Map(oldResult.rows.map((row) => [row.seq, row]));
    const newBySeq = new Map(newRows.map((row) => [row.seq, row]));
    const rows = csvRows.map((csvRow) => {
      const seq = Number(csvRow.seq);
      const oldRow = oldBySeq.get(seq) || {};
      const newRow = newBySeq.get(seq) || {};
      const status = oldRow.menu_visible && oldRow.field_match && newRow.page_opened && newRow.field_match ? 'PASS' : 'FAIL';
      return {
        seq,
        old_name: normalize(csvRow.name),
        new_name: newRow.name || '',
        old_menu_visible: Boolean(oldRow.menu_visible),
        old_field_match: Boolean(oldRow.field_match),
        new_page_opened: Boolean(newRow.page_opened),
        new_row_count: Number(newRow.row_count || 0),
        new_field_match: Boolean(newRow.field_match),
        new_error: newRow.error || '',
        status,
      };
    });
    const failures = rows.filter((row) => row.status !== 'PASS');
    const report = {
      status: failures.length ? 'FAIL' : 'PASS',
      frontend_url: FRONTEND_URL,
      db_name: DB_NAME,
      old_base_url: OLD_BASE_URL,
      old_user: {
        UserId: oldResult.user.UserId,
        UserName: oldResult.user.UserName,
        PersonName: oldResult.user.PersonName,
        CompanyName: oldResult.user.CompanyName,
        ProjectName: oldResult.user.ProjectName,
      },
      new_user: NEW_LOGIN,
      row_count: rows.length,
      failure_count: failures.length,
      failures,
      rows,
      old_rows: oldResult.rows,
      new_rows: newRows,
      artifact_dir: OUT_DIR,
    };
    writeJson('summary.json', report);
    writeMarkdown(report);
    console.log(`[scbs55_old_new_browser_surface_compare] ${report.status} artifacts=${OUT_DIR}`);
    if (failures.length) process.exitCode = 1;
  } finally {
    await browser.close().catch(() => undefined);
  }
}

main().catch((err) => {
  ensureDir(OUT_DIR);
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[scbs55_old_new_browser_surface_compare] FAIL ${err.message}`);
  console.error(`[scbs55_old_new_browser_surface_compare] artifacts=${OUT_DIR}`);
  process.exit(1);
});
