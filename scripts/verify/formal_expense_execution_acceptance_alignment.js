#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

function loadPlaywright() {
  const candidates = [
    path.join(process.cwd(), 'frontend/apps/web/package.json'),
    path.join(process.cwd(), 'package.json'),
    '/tmp/sc-pw/package.json',
  ];
  for (const candidate of candidates) {
    if (!fs.existsSync(candidate)) continue;
    try {
      return createRequire(candidate)('playwright');
    } catch (_err) {
      // Try the next known install location.
    }
  }
  return require('playwright');
}

const { chromium } = loadPlaywright();

const FRONTEND_URL = (process.env.FRONTEND_URL || 'http://1.95.85.92:18081').replace(/\/$/, '');
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ACTION_ID_ENV = Number(process.env.ACTION_ID || 0);
const MENU_ID_ENV = Number(process.env.MENU_ID || 0);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts/verify';

const EXPECTED_COUNTS = {
  '供货合同': 851,
  '劳务合同': 187,
  '分包合同': 86,
  '机械合同（合同）': 221,
  '租赁合同': 221,
};
const EXPECTED_TOTAL = Object.values(EXPECTED_COUNTS).reduce((sum, value) => sum + value, 0);
const EXPECTED_HEADERS = [
  '单据状态',
  '单据编号',
  '项目名称',
  '签订日期',
  '标题',
  '往来单位',
  '合同内容',
  '合同类别',
  '合同金额',
  '已开票金额',
  '已付款金额',
  '未付款金额',
  '未开票金额',
  '合同编号',
  '附件',
  '录入人',
  '录入时间',
];
const FORMAL_DOMAIN = [
  '&',
  ['legacy_contract_id', 'ilike', 'direct_acceptance:%'],
  ['legacy_acceptance_label', 'in', Object.keys(EXPECTED_COUNTS)],
];
const FIELDS = [
  'id',
  'legacy_acceptance_label',
  'legacy_visible_document_state',
  'legacy_visible_document_no',
  'legacy_visible_project_name',
  'legacy_visible_contract_date',
  'legacy_visible_title',
  'legacy_visible_counterparty',
  'legacy_visible_engineering_content',
  'legacy_visible_category',
  'legacy_visible_amount',
  'legacy_visible_invoice_amount',
  'legacy_visible_received_amount',
  'legacy_visible_unreceived_amount',
  'legacy_visible_invoice_unreceived_amount',
  'legacy_visible_contract_no',
  'legacy_visible_attachment',
  'legacy_visible_creator_name',
  'legacy_visible_created_time',
];

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'formal-expense-execution-alignment', ts);

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  if (await inputs.nth(2).isEnabled().catch(() => false)) {
    await inputs.nth(2).fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 });
}

async function authToken(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intentRequest(page, intent, params, anonymous = false) {
  const token = anonymous ? '' : await authToken(page);
  const response = await page.evaluate(async ({ dbName, bearer, intentName, payload, anonymous }) => {
    const headers = {
      'Content-Type': 'application/json',
      'X-Odoo-DB': dbName,
      'X-Trace-Id': `formal-expense-execution-alignment-${Date.now()}`,
    };
    if (anonymous) {
      headers['X-Anonymous-Intent'] = '1';
    } else if (bearer) {
      headers.Authorization = `Bearer ${bearer}`;
    }
    const resp = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ intent: intentName, params: { db: dbName, ...payload } }),
    });
    const body = await resp.json().catch(() => ({}));
    return { status: resp.status, body };
  }, { dbName: DB_NAME, bearer: token, intentName: intent, payload: params, anonymous });
  if (response.body?.ok !== true) {
    throw new Error(`${intent} failed: ${JSON.stringify(response.body?.error || response.body).slice(0, 1000)}`);
  }
  return response.body.data || {};
}

function walkMenus(nodes, visitor) {
  if (!Array.isArray(nodes)) return;
  for (const node of nodes) {
    visitor(node);
    walkMenus(node.children, visitor);
  }
}

async function resolveFormalAction(page) {
  const init = await intentRequest(page, 'app.init', { scene: 'web', with_preload: false });
  const candidates = [];
  walkMenus(init.menus || init.nav || init.scenes || [], (node) => {
    const label = normalize(node.label || node.name || node.title);
    const meta = node.meta || node.target || {};
    const actionId = Number(meta.action_id || node.action_id || 0);
    if ((label === '支出合同执行' || actionId === ACTION_ID_ENV) && actionId) {
      candidates.push({
        actionId,
        menuId: Number(node.menu_id || node.id || meta.menu_id || 0),
        source: 'app.init',
      });
    }
  });
  if (ACTION_ID_ENV) {
    const matched = candidates.find((candidate) => candidate.actionId === ACTION_ID_ENV);
    return {
      actionId: ACTION_ID_ENV,
      menuId: MENU_ID_ENV || matched?.menuId || 0,
      source: matched ? 'env+app.init' : 'env',
    };
  }
  if (!candidates.length) {
    throw new Error('cannot resolve formal 支出合同执行 action from app.init; set ACTION_ID/MENU_ID');
  }
  return candidates[candidates.length - 1];
}

async function openFormalList(page, action) {
  const url = `${FRONTEND_URL}/a/${action.actionId}${action.menuId ? `?menu_id=${action.menuId}` : ''}`;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('.template-layout-shell, body').first().waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    return !text.includes('正在加载页面') && !text.includes('Loading');
  }, null, { timeout: 45000 });
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    return text.includes('支出合同执行视图列表')
      && text.includes('单据状态')
      && !text.includes('当前视图使用可读降级渲染');
  }, null, { timeout: 45000 });
  await page.screenshot({ path: path.join(outDir, 'formal-expense-execution.png'), fullPage: true });
  return url;
}

async function renderedText(page) {
  return normalize(await page.locator('body').evaluate((node) => node.textContent || ''));
}

async function renderedHeaderTexts(page) {
  const selectors = [
    'table thead th',
    '[role="columnheader"]',
    '.table-header',
    '.list-header',
    '.data-table-header',
    '.field-header',
  ];
  const values = [];
  for (const selector of selectors) {
    const rows = await page.locator(selector).evaluateAll((nodes) => nodes.map((node) => String(node.textContent || '').trim()).filter(Boolean)).catch(() => []);
    values.push(...rows);
  }
  return Array.from(new Set(values.map(normalize).filter(Boolean)));
}

async function fetchFormalRows(page) {
  const data = await intentRequest(page, 'api.data', {
    op: 'list',
    model: 'construction.contract.expense',
    domain: FORMAL_DOMAIN,
    fields: FIELDS,
    limit: 2000,
    offset: 0,
    order: 'legacy_acceptance_label asc, id asc',
    need_total: true,
    group_by: ['legacy_acceptance_label'],
    need_group_total: true,
    group_limit: 20,
  });
  return {
    records: Array.isArray(data.records) ? data.records : [],
    total: Number(data.total || 0),
    groups: Array.isArray(data.group_summary) ? data.group_summary : [],
  };
}

function countByLabel(records) {
  const counts = {};
  for (const row of records) {
    const label = normalize(row.legacy_acceptance_label);
    counts[label] = (counts[label] || 0) + 1;
  }
  return counts;
}

function assertCondition(condition, message, context, errors) {
  if (!condition) errors.push({ message, context });
}

function hasAny(row, fields) {
  return fields.some((field) => normalize(row[field]));
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const executablePath = process.env.PLAYWRIGHT_EXECUTABLE_PATH || process.env.CHROMIUM_PATH || '';
  const browser = await chromium.launch({
    headless: true,
    ...(executablePath ? { executablePath } : {}),
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: 'zh-CN' });
  const errors = [];
  const summary = {
    pass: false,
    base_url: FRONTEND_URL,
    db: DB_NAME,
    login: LOGIN,
    expected_total: EXPECTED_TOTAL,
    expected_counts: EXPECTED_COUNTS,
    artifact_dir: outDir,
  };

  try {
    await login(page);
    const action = await resolveFormalAction(page);
    summary.action = action;
    summary.url = await openFormalList(page, action);

    const bodyText = await renderedText(page);
    const headers = await renderedHeaderTexts(page);
    summary.rendered_headers = headers;
    summary.rendered_text_excerpt = bodyText.slice(0, 1000);
    for (const header of EXPECTED_HEADERS) {
      assertCondition(
        headers.includes(header) || bodyText.includes(header),
        `formal list missing header: ${header}`,
        { header },
        errors,
      );
    }

    const formal = await fetchFormalRows(page);
    writeJson('formal_rows_sample.json', {
      total: formal.total,
      groups: formal.groups,
      sample: formal.records.slice(0, 20),
    });
    summary.total = formal.total;
    summary.record_count_fetched = formal.records.length;
    summary.counts_by_label = countByLabel(formal.records);
    summary.group_summary = formal.groups;

    assertCondition(formal.total === EXPECTED_TOTAL, 'formal list total does not match accepted projection', { actual: formal.total }, errors);
    assertCondition(formal.records.length === EXPECTED_TOTAL, 'formal list fetched rows do not cover all accepted rows', { actual: formal.records.length }, errors);
    for (const [label, expected] of Object.entries(EXPECTED_COUNTS)) {
      const actual = summary.counts_by_label[label] || 0;
      assertCondition(actual === expected, 'formal label count mismatch', { label, expected, actual }, errors);
    }
    const extraLabels = Object.keys(summary.counts_by_label).filter((label) => !(label in EXPECTED_COUNTS));
    assertCondition(extraLabels.length === 0, 'formal list contains labels outside accepted projection', { extraLabels }, errors);

    const criticalFailures = [];
    for (const row of formal.records) {
      const rowFailures = [];
      for (const field of ['legacy_acceptance_label', 'legacy_visible_document_state', 'legacy_visible_document_no']) {
        if (!normalize(row[field])) rowFailures.push(field);
      }
      if (!hasAny(row, ['legacy_visible_project_name', 'legacy_visible_counterparty'])) {
        rowFailures.push('project_or_counterparty');
      }
      if (!hasAny(row, ['legacy_visible_title', 'legacy_visible_engineering_content', 'legacy_visible_contract_no'])) {
        rowFailures.push('title_or_content_or_contract_no');
      }
      if (rowFailures.length) {
        criticalFailures.push({ id: row.id, label: row.legacy_acceptance_label, missing: rowFailures });
      }
    }
    assertCondition(
      criticalFailures.length === 0,
      'formal list has rows missing critical accepted visible fields',
      { count: criticalFailures.length, sample: criticalFailures.slice(0, 20) },
      errors,
    );

    summary.errors = errors;
    summary.pass = errors.length === 0;
    writeJson('summary.json', summary);
  } finally {
    await browser.close();
  }

  if (!summary.pass) {
    console.error(`[formal_expense_execution_acceptance_alignment] FAIL ${JSON.stringify(errors, null, 2)}`);
    console.error(`[formal_expense_execution_acceptance_alignment] artifacts: ${outDir}`);
    process.exit(1);
  }
  console.log('[formal_expense_execution_acceptance_alignment] PASS');
  console.log(JSON.stringify({
    action: summary.action,
    total: summary.total,
    counts_by_label: summary.counts_by_label,
    artifact_dir: outDir,
  }, null, 2));
}

main().catch((err) => {
  console.error(`[formal_expense_execution_acceptance_alignment] FAIL: ${err.message}`);
  process.exit(1);
});
